from django import forms
from datetime import datetime, date
import jdatetime
from django.templatetags.static import static
import re
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe

class PersianDateInput(forms.DateInput):
    """
    A custom widget for handling Persian (Jalali) dates in Django forms.
    Displays dates in Persian format (YYYY/MM/DD) and stores them in Gregorian format.
    Integrates with persian-datepicker.js for a better user experience.
    """
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control form-control-lg date',
            'data-jdp': 'data-jdp',
            'autocomplete': 'off',
            'placeholder': 'تاریخ ',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs, format='%Y/%m/%d')

    def format_value(self, value):
        """
        Convert Gregorian date to Persian (Jalali) date for display.
        """
        if value and isinstance(value, (datetime, date, str)):
            try:
                if isinstance(value, str):
                    # Parse string to datetime if needed
                    value = datetime.strptime(value, '%Y-%m-%d')
                elif isinstance(value, datetime):
                    value = value.date()
                # Convert Gregorian to Jalali
                jalali_date = jdatetime.date.fromgregorian(date=value)
                return jalali_date.strftime('%Y/%m/%d')
            except (ValueError, TypeError):
                return value
        return value

    def get_context(self, name, value, attrs):
        """
        Ensure Persian date is rendered in templates.
        """
        context = super().get_context(name, value, attrs)
        context['widget']['value'] = self.format_value(value)
        return context

    def value_from_datadict(self, data, files, name):
        """
        Convert Persian date input to Gregorian for form processing.
        """
        value = super().value_from_datadict(data, files, name)
        if value:
            try:
                # Expect input in format like '1403/12/05'
                year, month, day = map(int, value.split('/'))
                # Convert Jalali to Gregorian
                gregorian_date = jdatetime.JalaliToGregorian(year, month, day).getGregorianList()
                return date(*gregorian_date)
            except (ValueError, TypeError):
                raise forms.ValidationError(
                    "فرمت تاریخ نامعتبر است. لطفاً تاریخ را به صورت 1403/12/05 وارد کنید."
                )
        return value

    class Media:
        # استفاده از static() برای تولید آدرس درست در همه محیط‌ها
        css = {
            'all': (
                static('plugins/jalalidatepicker/jalalidatepicker.css'),
            )
        }
        js = (
            static('plugins/jalalidatepicker/jalalidatepicker.js'),
        )



class PersianPhoneInput(forms.TextInput):
    """
    ویجیت اختصاصی برای شماره موبایل ایرانی
    - فقط 11 رقم عددی
    - باید با 09 شروع شود
    - ورودی غیرعددی را بلاک می‌کند
    """

    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control text-center',
            'placeholder': '۰۹۱۲۳۴۵۶۷۸۹',
            'maxlength': '11',
            'minlength': '11',
            'inputmode': 'numeric',  # کیبورد عددی در موبایل
            'pattern': '[0-9]{11}',  # برای اعتبارسنجی HTML5
            'dir': 'ltr',  # چون اعداد لاتین هستند
        }
        if attrs:
            default_attrs.update(attrs)

        super().__init__(attrs=default_attrs)

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        # اضافه کردن event برای جلوگیری از ورودی غیرعددی
        attrs.setdefault('oninput', "this.value = this.value.replace(/[^0-9]/g, '')")
        attrs.setdefault('onkeypress', "return event.charCode >= 48 && event.charCode <= 57")
        return attrs


# اختیاری: اعتبارسنجی قوی‌تر در سطح فیلد فرم
phone_validator = RegexValidator(
    regex=r'^09\d{9}$',
    message=_("شماره موبایل باید ۱۱ رقم باشد و با ۰۹ شروع شود."),
    code='invalid_phone'
)


class PasswordStrengthInput(forms.PasswordInput):
    """
    ویجیت پیشرفته رمز عبور با:
    - نمایش قدرت رمز و چک‌لیست قوانین (فقط برای فیلد اصلی)
    - آیکون چشم برای نمایش/مخفی کردن رمز
    - نشانگر تطابق زنده برای فیلد تکرار (بدون قوانین قدرت)
    """

    def __init__(self, attrs=None, is_confirm=False):
        """
        is_confirm: اگر True باشد، این فیلد تکرار رمز است و فقط نشانگر تطابق + چشم دارد
        """
        self.is_confirm = is_confirm

        default_attrs = {
            'class': 'form-control pe-5',  # فضای کافی برای آیکون چشم
            'placeholder': 'رمز عبور را وارد کنید' if not is_confirm else 'رمز عبور را تکرار کنید',
            'autocomplete': 'new-password' if not is_confirm else 'off',
        }
        if attrs:
            default_attrs.update(attrs)

        super().__init__(attrs=default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        input_html = super().render(name, value, attrs, renderer)
        input_id = attrs.get('id', f'id_{name}')

        # دکمه چشم برای نمایش/مخفی کردن رمز
        eye_button = f'''
        <button type="button" class="btn btn-outline-secondary position-absolute end-0 top-50 translate-middle-y password-toggle"
                style="border: none; background: transparent; height: 100%; z-index: 10;"
                onclick="togglePasswordVisibility('{input_id}')">
            <i class="fas fa-eye" id="eye-icon-{input_id}"></i>
        </button>
        '''

        base_html = f'''
        <div class="password-strength-widget position-relative">
            <div class="position-relative">
                {input_html}
                {eye_button}
            </div>
        '''

        # فقط برای فیلد اصلی رمز عبور: progress bar + قوانین
        if not self.is_confirm:
            base_html += f'''
            <!-- Progress Bar -->
            <div class="progress mt-2" style="height: 6px;">
                <div class="progress-bar bg-danger" role="progressbar" style="width: 0%;"
                     id="strength-bar-{input_id}"></div>
            </div>

            <!-- Strength Label -->
            <small class="text-muted d-block mt-1" id="strength-text-{input_id}">
                رمز عبور خود را وارد کنید
            </small>

            <!-- Rules Checklist -->
            <ul class="list-unstyled small mt-3 mb-0 password-rules" id="rules-{input_id}">
                <li data-rule="length">حداقل ۸ کاراکتر</li>
                <li data-rule="lowercase">حداقل یک حرف کوچک (a-z)</li>
                <li data-rule="uppercase">حداقل یک حرف بزرگ (A-Z)</li>
                <li data-rule="number">حداقل یک عدد (0-9)</li>
                <li data-rule="special">حداقل یک کاراکتر ویژه (@#$%^&*...)</li>
            </ul>
            '''

        # فقط برای فیلد تکرار: نشانگر تطابق
        else:
            base_html += f'''
            <div class="mt-3 text-center" id="confirm-match-{input_id}" style="display: none;">
                <span class="text-danger"><i class="fas fa-times-circle fa-lg"></i> رمزهای عبور مطابقت ندارند</span>
            </div>
            '''

        base_html += '''
        </div>
        '''

        return mark_safe(base_html)

    class Media:
        css = {
            'all': (static('css/password_strength.css'),)
        }
        js = (
            static('js/password_strength.js'),
        )