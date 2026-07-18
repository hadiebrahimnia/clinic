from django.utils.safestring import mark_safe
from django.urls import reverse
from urllib.parse import urlencode 
from django.template import Template, Context
import math
from django.db import models
from django.db.models.functions import Coalesce

# ====================== Helper Functions ======================
def get_user_status(psychologist=None, request=None):
    """
    وضعیت کاربر: لاگین، مالکیت و نقش‌ها
    """
    if not request or not hasattr(request, 'user'):
        return {
            'is_authenticated': False,
            'is_owner': False,
        }

    user = request.user
    if not user.is_authenticated:
        return {
            'is_authenticated': False,
            'is_owner': False,
        }

    result = {
        'is_authenticated': True,
        'is_owner': False,
    }

    # if hasattr(user, 'roles'):
    #     result['roles'] = list(
    #         user.roles.annotate(
    #             display_name=Coalesce('name_fa', 'name_en')
    #         ).values_list('display_name', flat=True)
    #     )

    if psychologist and hasattr(psychologist, 'profile'):
        if psychologist.profile == user:
            result['is_owner'] = True

    return result






def get_profile_status(request=None):
    """
    وضعیت کامل پروفایل کاربر را برمی‌گرداند.
    کاملاً مستقل از مدل Profile — فقط از request.user استفاده می‌کند.
    """
    if not request or not hasattr(request, 'user'):
        return {
            'is_authenticated': False,
        }

    user = request.user

    if not user.is_authenticated:
        return {
            'is_authenticated': False,
        }

    result = {
        'is_authenticated': True,
        'username': user.username,
        'email': getattr(user, 'email', None),
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'access_level': getattr(user, 'access_level', 'basic'),
    }

    # نقش‌ها (با پشتیبانی از نام چندزبانه)
    if hasattr(user, 'roles') and user.roles.exists():
        result['roles'] = list(
            user.roles.annotate(
                display_name=Coalesce('name_en','name_fa')
            ).values_list('display_name', flat=True)
        )
    else:
        result['roles'] = []

    # وضعیت تکمیل پروفایل
    if hasattr(user, 'is_profile_complete'):
        result['is_profile_complete'] = user.is_profile_complete
    else:
        # fallback ساده در صورتی که متد وجود نداشت
        result['is_profile_complete'] = bool(
            getattr(user, 'phone_number', None) and
            getattr(user, 'date_of_birth', None) and
            getattr(user, 'gender', None)
        )

    # مجوزهای کلی (اختیاری اما مفید)
    result['permissions'] = list(user.get_all_permissions()) if hasattr(user, 'get_all_permissions') else []

    return result