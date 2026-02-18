import datetime
import decimal
import json

from django.db.models.signals import (
    pre_save,
    post_save,
    post_delete,
    m2m_changed,
    pre_delete,
)
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.forms.models import model_to_dict
from django.utils import timezone
from django.db import models
from core.models import Logs
# from appreserve.models import Turn, Plan, Relative
from core.middleware import get_current_profile


# =====================================================
# تنظیمات
# =====================================================

LOGGED_MODELS = [
    "Turn",
    "Plan",
]

EXCLUDED_FIELDS = {"id"}
MERGE_TIME_WINDOW_SECONDS = 5

_old_instances = {}
_m2m_request_buffer = {}
_deleted_m2m_cache = {}


# =====================================================
# ابزارهای کمکی عمومی
# =====================================================

def normalize_empty(value):
    if value in ("", [], {}, ()):
        return None
    return value

def make_json_serializable(value):
    if isinstance(value, (datetime.date, datetime.datetime, datetime.time)):
        return value.isoformat()

    if isinstance(value, decimal.Decimal):
        return float(value)

    if isinstance(value, (list, tuple)):
        return [make_json_serializable(v) for v in value]

    if isinstance(value, dict):
        return {
            k: make_json_serializable(v)
            for k, v in value.items()
        }

    return value


def dict_serializable(data):
    return {
        k: make_json_serializable(v)
        for k, v in data.items()
        if k not in EXCLUDED_FIELDS and v not in (None, "", [], {}, ())
    }


def get_content_type(model):
    return ContentType.objects.get_for_model(model)


def get_last_log(model, instance):
    return (
        Logs.objects
        .filter(
            content_type=get_content_type(model),
            object_id=instance.pk,
            action__in=["create", "update"],
        )
        .order_by("-id")
        .first()
    )


def get_last_timestamp(model, instance):
    log = get_last_log(model, instance)
    if not log:
        return None
    return log.changes.get("timestamp_change", {}).get("new")


def get_m2m_field_name(instance, sender):
    for field in instance._meta.many_to_many:
        if field.remote_field.through == sender:
            return field.name
    return None

# =====================================================
# نمایش سفارشی مقادیر (اختصاصی برای هر فیلد)
# =====================================================

CUSTOM_FIELD_DISPLAY = {
    # Plan
    
}

def humanize_value(instance, field_name, value):
    """تبدیل مقدار به متن خوانا با منطق سفارشی یا عمومی"""
    if value in (None, "", [], {}, ()):
        return "—"

    # 🎯 منطق اختصاصی
    if field_name in CUSTOM_FIELD_DISPLAY:
        try:
            return CUSTOM_FIELD_DISPLAY[field_name](value)
        except Exception:
            return value

    # ⚙️ fallback عمومی
    try:
        field = instance._meta.get_field(field_name)
    except Exception:
        return value

    # اگر choices دارد
    if getattr(field, "choices", None):
        return dict(field.choices).get(value, value)

    # اگر ForeignKey است
    if isinstance(field, models.ForeignKey):
        try:
            related_obj = field.related_model.objects.filter(pk=value).first()
            return str(related_obj) if related_obj else "—"
        except Exception:
            return value

    # اگر لیست (M2M)
    if isinstance(value, list):
        return ", ".join(map(str, value))

    return value


def humanize_changes(instance, changes_dict):
    """خواناسازی تمام old/new در changes"""
    result = {}
    for field, values in changes_dict.items():
        if field == "timestamp_change":
            result[field] = values
            continue

        if isinstance(values, dict) and "old" in values and "new" in values:
            result[field] = {
                "old": humanize_value(instance, field, values["old"]),
                "new": humanize_value(instance, field, values["new"]),
            }
        else:
            result[field] = values
    return result


# =====================================================
# PRE SAVE
# =====================================================

@receiver(pre_save)
def capture_old_instance(sender, instance, **kwargs):
    if sender == Logs:
        return
    if sender.__name__ not in LOGGED_MODELS:
        return
    if not instance.pk:
        return

    try:
        _old_instances[(sender, instance.pk)] = model_to_dict(
            sender.objects.get(pk=instance.pk)
        )
    except sender.DoesNotExist:
        pass


# =====================================================
# POST SAVE – CREATE / UPDATE
# =====================================================

@receiver(post_save)
def create_or_update_log(sender, instance, created, **kwargs):
    if sender == Logs:
        return
    if sender.__name__ not in LOGGED_MODELS:
        return

    now = timezone.now().isoformat()
    profile = get_current_profile()
    content_type = get_content_type(sender)
    cache_key = (sender, instance.pk)

    # ---------------- CREATE ----------------
    if created:
        raw_data = dict_serializable(model_to_dict(instance))
        changes = {k: {"old": None, "new": v} for k, v in raw_data.items()}
        changes["timestamp_change"] = {"old": None, "new": now}

        changes = humanize_changes(instance, changes)

        Logs.objects.create(
            profile=profile,
            action="create",
            content_type=content_type,
            object_id=instance.pk,
            changes=changes,
        )
        return

    # ---------------- UPDATE ----------------
    old_data = _old_instances.pop(cache_key, {})
    new_data = model_to_dict(instance)
    changes = {}

    for field, old_value in old_data.items():
        if field in EXCLUDED_FIELDS:
            continue

        new_value = new_data.get(field)

        if normalize_empty(old_value) != normalize_empty(new_value):
            changes[field] = {
                "old": make_json_serializable(old_value),
                "new": make_json_serializable(new_value),
            }

    if not changes:
        return

    changes["timestamp_change"] = {
        "old": get_last_timestamp(sender, instance),
        "new": now,
    }

    # ✨ خواناسازی
    changes = humanize_changes(instance, changes)

    Logs.objects.create(
        profile=profile,
        action="update",
        content_type=content_type,
        object_id=instance.pk,
        changes=changes,
    )


# =====================================================
# M2M – قواعد create / update
# =====================================================

@receiver(m2m_changed)
def handle_m2m_change(sender, instance, action, reverse, model, pk_set, **kwargs):
    if instance.__class__.__name__ not in LOGGED_MODELS:
        return

    if not instance.pk:
        return

    field_name = get_m2m_field_name(instance, sender)
    if not field_name:
        return

    key = (instance.__class__, instance.pk, field_name)

    # ---------- PRE ----------
    if action in ("pre_add", "pre_remove", "pre_clear"):
        if key not in _m2m_request_buffer:
            _m2m_request_buffer[key] = {
                "old": list(
                    getattr(instance, field_name)
                    .values_list("pk", flat=True)
                ),
                "new": None,
            }
        return

    # ---------- POST ----------
    if action not in ("post_add", "post_remove", "post_clear"):
        return

    if key not in _m2m_request_buffer:
        return

    _m2m_request_buffer[key]["new"] = list(
        getattr(instance, field_name)
        .values_list("pk", flat=True)
    )

    data = _m2m_request_buffer.pop(key)
    if data["old"] == data["new"]:
        return

    model_class = instance.__class__
    now_dt = timezone.now()
    now_iso = now_dt.isoformat()
    last_log = get_last_log(model_class, instance)

    if last_log and last_log.action == "create":
        updated = last_log.changes
        updated[field_name] = data
        updated = humanize_changes(instance, updated)
        last_log.changes = updated
        last_log.save(update_fields=["changes"])
        return

    if last_log and last_log.action == "update" and last_log.timestamp:
        delta = (now_dt - last_log.timestamp).total_seconds()
        if delta <= MERGE_TIME_WINDOW_SECONDS:
            updated = last_log.changes
            updated[field_name] = data
            updated = humanize_changes(instance, updated)
            last_log.changes = updated
            last_log.save(update_fields=["changes"])
            return

    data = humanize_changes(instance, {field_name: data})
    Logs.objects.create(
        profile=get_current_profile(),
        action="update",
        content_type=get_content_type(model_class),
        object_id=instance.pk,
        changes={
            field_name: data[field_name],
            "timestamp_change": {
                "old": get_last_timestamp(model_class, instance),
                "new": now_iso,
            },
        },
    )


# =====================================================
# DELETE
# =====================================================

@receiver(pre_delete)
def capture_m2m_before_delete(sender, instance, **kwargs):
    if sender == Logs:
        return
    if sender.__name__ not in LOGGED_MODELS:
        return
    if not instance.pk:
        return

    key = (sender, instance.pk)
    m2m_data = {}

    for field in instance._meta.many_to_many:
        m2m_data[field.name] = list(
            getattr(instance, field.name).values_list("pk", flat=True)
        )

    _deleted_m2m_cache[key] = m2m_data


@receiver(post_delete)
def delete_log(sender, instance, **kwargs):
    if sender == Logs:
        return
    if sender.__name__ not in LOGGED_MODELS:
        return

    key = (sender, instance.pk)
    raw_data = model_to_dict(instance)

    # گرفتن داده‌های M2M قبل از حذف
    m2m_data = _deleted_m2m_cache.pop(key, {})
    for field_name, value in m2m_data.items():
        raw_data[field_name] = value

    # ساختار old/new برای تمام فیلدها
    changes = {k: {"old": make_json_serializable(v), "new": None} for k, v in raw_data.items() if k not in EXCLUDED_FIELDS}

    # timestamp_change
    changes["timestamp_change"] = {
        "old": get_last_timestamp(sender, instance),
        "new": timezone.now().isoformat(),
    }

    # خواناسازی مقادیر با humanize
    changes = humanize_changes(instance, changes)

    Logs.objects.create(
        profile=get_current_profile(),
        action="delete",
        content_type=get_content_type(sender),
        object_id=instance.pk,
        changes=changes,
    )


# -------------------------------
# 🔹 ترجمه نام فیلد و مقادیر برای پنل
# -------------------------------
FIELD_NAME_TRANSLATIONS = {
    # Plan
    
}

def translate_field_name(field_name: str) -> str:
    return FIELD_NAME_TRANSLATIONS.get(field_name, field_name)

VALUE_TRANSLATIONS = {
    
}

def translate_value(value):
    if value is None:
        return '—'
    if isinstance(value, list):
        return ', '.join(str(translate_value(v)) for v in value)
    if isinstance(value, dict):
        return json.dumps({k: translate_value(v) for k, v in value.items()}, ensure_ascii=False)
    if value in VALUE_TRANSLATIONS:
        return VALUE_TRANSLATIONS[value]
    if isinstance(value, bool):
        return 'بله' if value else 'خیر'
    return value


from datetime import datetime as py_datetime
def to_jalali_display(dt_or_iso_str):
    """
    تبدیل datetime یا رشته ISO به نمایش شمسی
    اگر jdatetime موجود نبود → فقط رشته خام برمی‌گرداند
    """
    if not dt_or_iso_str:
        return "—"

    # تبدیل به datetime اگر رشته باشد
    if isinstance(dt_or_iso_str, str):
        try:
            dt = py_datetime.fromisoformat(dt_or_iso_str.replace("Z", "+00:00"))
        except Exception:
            return dt_or_iso_str[:19].replace("T", " ")  # fallback خام
    elif isinstance(dt_or_iso_str, py_datetime):
        dt = dt_or_iso_str
    else:
        return "—"

    try:
        import jdatetime
        jdt = jdatetime.datetime.fromgregorian(datetime=dt)
        return jdt.strftime("%Y/%m/%d - %H:%M")
    except (ImportError, Exception):
        # اگر jdatetime نبود → نمایش میلادی ساده
        return dt.strftime("%Y-%m-%d %H:%M")