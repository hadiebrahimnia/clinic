from django import template

from core.jalali import (
    gregorian_date_to_jalali,
    gregorian_to_jalali,
    jalali_to_gregorian,
    jalali_to_gregorian_datetime,
)

register = template.Library()


@register.filter(name="to_jalali")
def to_jalali(value, fmt=None):
    """تبدیل datetime/date میلادی به رشته شمسی."""
    return gregorian_to_jalali(value, fmt=fmt)


@register.filter(name="to_jalali_date")
def to_jalali_date(value, fmt="%Y/%m/%d"):
    """تبدیل تاریخ میلادی به تاریخ شمسی (بدون زمان)."""
    return gregorian_date_to_jalali(value, fmt=fmt)


@register.filter(name="to_gregorian")
def to_gregorian(value, fmt=None):
    """تبدیل تاریخ/زمان شمسی به میلادی."""
    return jalali_to_gregorian(value, fmt=fmt)


@register.filter(name="to_gregorian_datetime")
def to_gregorian_datetime(value, fmt=None):
    """تبدیل تاریخ/زمان شمسی به datetime میلادی."""
    return jalali_to_gregorian_datetime(value, fmt=fmt)
