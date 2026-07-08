"""
تبدیل تاریخ و زمان بین شمسی (جلالی) و میلادی (گرگوری)

توابع اصلی:
    gregorian_to_jalali   -> تبدیل میلادی به شمسی
    jalali_to_gregorian   -> تبدیل شمسی به میلادی

برای استفاده در قالب‌های Django، یک template tag نیز ثبت شده است
(نگاه کنید به core/templatetags/jdate.py):

    {% load jdate %}
    {{ some_datetime|to_jalali }}            -> 1405/04/17 - 12:30
    {{ some_datetime|to_jalali:"%Y/%m/%d" }} -> 1405/04/17
    {{ some_date|to_jalali_date }}           -> 1405/04/17
"""

import datetime

import jdatetime


# ====================== Gregorian -> Jalali ======================
def gregorian_to_jalali(value, fmt=None):
    """
    تبدیل datetime یا date میلادی به شمسی.

    value: datetime.datetime | datetime.date | رشته ISO
    fmt:  الگوی strftime شمسی (پیش‌فرض '%Y/%m/%d - %H:%M' برای datetime
          و '%Y/%m/%d' برای date)
    """
    if value in (None, ""):
        return None

    if isinstance(value, str):
        value = _parse_gregorian_string(value)

    if isinstance(value, datetime.datetime):
        jdt = jdatetime.datetime.fromgregorian(datetime=value)
        return jdt.strftime(fmt or "%Y/%m/%d - %H:%M")
    if isinstance(value, datetime.date):
        jd = jdatetime.date.fromgregorian(date=value)
        return jd.strftime(fmt or "%Y/%m/%d")

    return value


def gregorian_date_to_jalali(value, fmt="%Y/%m/%d"):
    """تبدیل فقط بخش تاریخ میلادی به شمسی (بدون زمان)."""
    return gregorian_to_jalali(value, fmt=fmt)


# ====================== Jalali -> Gregorian ======================
def jalali_to_gregorian(year, month=None, day=None, fmt=None):
    """
    تبدیل شمسی به میلادی.

    می‌توان سه آرگومان عددی (year, month, day) داد،
    یا یک jdatetime/JalaliDate/رشته شمسی.

    خروجی: datetime.datetime | datetime.date | رشته فرمت‌شده
    """
    if year is None:
        return None

    if isinstance(year, (jdatetime.datetime, jdatetime.date)):
        gdt = year.togregorian()
        return gdt.strftime(fmt) if fmt else gdt

    if isinstance(year, str) and month is None:
        jd = _parse_jalali_string(year)
        gdt = jd.togregorian()
        if isinstance(jd, jdatetime.datetime):
            return gdt.strftime(fmt or "%Y-%m-%d %H:%M") if fmt else gdt
        return gdt.strftime(fmt or "%Y-%m-%d") if fmt else gdt

    if None in (month, day):
        return None

    g_list = jdatetime.JalaliToGregorian(int(year), int(month), int(day)).getGregorianList()
    gdate = datetime.date(g_list[0], g_list[1], g_list[2])
    return gdate.strftime(fmt) if fmt else gdate


def jalali_to_gregorian_datetime(year, month=None, day=None, hour=0, minute=0, second=0, fmt=None):
    """تبدیل شمسی (با زمان) به datetime میلادی."""
    if isinstance(year, (jdatetime.datetime, jdatetime.date)):
        gdt = year.togregorian()
        return gdt.strftime(fmt) if fmt else gdt
    if isinstance(year, str) and month is None:
        jdt = _parse_jalali_string(year)
        gdt = jdt.togregorian()
        return gdt.strftime(fmt or "%Y-%m-%d %H:%M") if fmt else gdt
    if None in (month, day):
        return None
    g_list = jdatetime.JalaliToGregorian(int(year), int(month), int(day)).getGregorianList()
    gdt = datetime.datetime(g_list[0], g_list[1], g_list[2], hour, minute, second)
    return gdt.strftime(fmt) if fmt else gdt


# ====================== Helpers ======================
def _parse_gregorian_string(s):
    s = s.replace("Z", "+00:00")
    try:
        return datetime.datetime.fromisoformat(s)
    except ValueError:
        return datetime.datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S")


def _parse_jalali_string(s):
    s = s.strip()
    if " " in s or ":" in s:
        return jdatetime.datetime.strptime(s, "%Y/%m/%d %H:%M")
    jd = jdatetime.datetime.strptime(s, "%Y/%m/%d")
    return jd.date()
