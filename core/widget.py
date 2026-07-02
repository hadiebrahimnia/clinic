from django import forms
from datetime import datetime, date
import jdatetime
from django.templatetags.static import static
import re
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.urls import reverse
from accounts.models import *

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

    
    class Media:
        
        js = (
            static('js/input-rules.js'),
        )

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


class ImageInput(forms.ClearableFileInput):
    """
    ویجت انتخاب عکس با تنظیمات قابل کنترل:
    - allowed_formats: ['jpg', 'png', 'jpeg', 'gif']
    - max_size_mb: حداکثر حجم فایل
    - min_width, min_height, max_width, max_height: محدودیت ابعاد
    """
    def __init__(self, attrs=None,
                 allowed_formats=None,
                 max_size_mb=None,
                 min_width=None, min_height=None,
                 max_width=None, max_height=None):
        self.allowed_formats = allowed_formats or ['jpg', 'jpeg', 'png']
        self.max_size_mb = max_size_mb or 2
        self.min_width = min_width or 200
        self.min_height = min_height or 200
        self.max_width = max_width or 4000
        self.max_height = max_height or 4000

        mime_types = ','.join([f'image/{ext}' for ext in self.allowed_formats])
        default_attrs = {
            'class': 'form-control-file d-none',
            'accept': mime_types,
            'data-allowed-formats': ','.join(self.allowed_formats),
            'data-max-size': str(self.max_size_mb),
            'data-min-width': str(self.min_width),
            'data-min-height': str(self.min_height),
            'data-max-width': str(self.max_width),
            'data-max-height': str(self.max_height),
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        input_html = super().render(name, value, attrs, renderer)
        input_id = attrs.get('id', f'id_{name}')
        has_image = bool(value and hasattr(value, 'url'))

        current_image_html = ''
        if has_image:
            current_image_html = f'''
            <img src="{value.url}" alt="تصویر فعلی" id="preview-{input_id}"
                 class="img-thumbnail mb-2 d-block" style="max-width: 180px; height: auto;">
            '''

        select_btn_class = '' if not has_image else 'd-none'
        remove_btn_class = 'd-none' if not has_image else ''

        html = f'''
        <div class="form-control text-center" >
            <div class="image-upload {select_btn_class}"  id="select-btn-{input_id}" onclick="document.getElementById('{input_id}').click()">
                <span>انتخاب تصویر</span>
                <i class="fa fa-upload"></i>
            </div>
            {current_image_html if has_image else f'<img id="preview-{input_id}" src="#" class="img-thumbnail mb-2 d-none" style="max-width: 180px; height: auto;">'}
            <div class="d-flex justify-content-center gap-2">
                <button type="button" id="remove-btn-{input_id}" class="btn btn-outline-danger btn-sm {remove_btn_class}"
                        onclick="clearImageSelection('{input_id}')">
                    <i class="fas fa-times-circle"></i> حذف
                </button>
            </div>
            {input_html}
        </div>
        '''

        return mark_safe(html)

    class Media:
        css = {
            'all': (
                static('css/imageinput.css'),
            )
        }
        js = (
            static('js/imageinput.js'),
        )

class ForeignKeySearchWidget(forms.Select):
    """
    ویجت اختصاصی ForeignKey با قابلیت جستجو
    بدون نیاز به پلاگین خارجی (Vanilla JS)
    """

    def __init__(self, attrs=None, placeholder='انتخاب کنید...'):
        default_attrs = {
            'class': 'fk-select d-none',  # مخفی می‌شود، نسخه سفارشی رندر می‌شود
            'data-placeholder': placeholder,
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        select_html = super().render(name, value, attrs, renderer)
        input_id = attrs.get('id', f'id_{name}')

        html = f"""
        <div class="fk-widget" id="wrapper-{input_id}">
            <div class="fk-display" onclick="toggleDropdown('{input_id}')">
                <span class="fk-placeholder">{self.attrs.get('data-placeholder', 'انتخاب کنید...')}</span>
                <span class="fk-selected"></span>
                <i class="fk-arrow"></i>
            </div>
            <div class="fk-dropdown" id="dropdown-{input_id}">
                <input type="text" class="fk-search" placeholder="جستجو...">
                <ul class="fk-options"></ul>
            </div>
            {select_html}
        </div>
        """
        return mark_safe(html)

    class Media:
        css = {'all': (static('css/foreignkey_widget.css'),)}
        js = (static('js/foreignkey_widget.js'),)



class ManyToManySearchWidget(forms.SelectMultiple):

    def __init__(self, attrs=None, placeholder="زمینه کاری را انتخاب کنید"):
        attrs = attrs or {}

        attrs.update({
            "class": "m2m-select d-none",
            "data-placeholder": placeholder,
        })

        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):

        select = super().render(name, value, attrs, renderer)

        input_id = attrs.get("id", f"id_{name}")

        return mark_safe(f"""
<div class="m2m-widget" id="wrapper-{input_id}">

    <div class="m2m-display">

        <div class="m2m-selected-items"></div>

        <span class="m2m-placeholder">
            {self.attrs["data-placeholder"]}
        </span>

        <span class="m2m-arrow"></span>

    </div>

    <div class="m2m-dropdown">

        <input
            class="m2m-search"
            type="text"
            placeholder="جستجو..."
        >

        <ul class="m2m-options"></ul>

    </div>

    {select}

</div>
""")

    class Media:
        css = {
            "all": (
                static("css/m2m_widget.css"),
            )
        }

        js = (
            static("js/m2m_widget.js"),
        )



class BooleanToggleWidget(forms.CheckboxInput):
    """
    ویجت سفارشی برای BooleanField
    نمایش به صورت دو دکمه چسبیده (مثل فعال / غیرفعال)
    """

    input_type = 'hidden'

    def __init__(self, attrs=None, label_true="فعال", label_false="غیرفعال"):
        self.label_true = label_true
        self.label_false = label_false
        default_attrs = {'class': 'boolean-button-widget'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        value = bool(value) if value is not None else False
        input_id = attrs.get('id', f'id_{name}')
        active_true = 'active' if value else ''
        active_false = '' if value else 'active'

        html = f"""
        <div class="boolean-button-group" id="wrapper-{input_id}">
            <input type="hidden" name="{name}" id="{input_id}" value="{int(value)}">
            <button type="button" class="boolean-btn left {active_true}"
                    data-value="1" onclick="toggleBooleanButtons('{input_id}', true)">
                {self.label_true}
            </button>
            <button type="button" class="boolean-btn right {active_false}"
                    data-value="0" onclick="toggleBooleanButtons('{input_id}', false)">
                {self.label_false}
            </button>
        </div>
        """
        return mark_safe(html)

    class Media:
        css = {'all': (static('css/boolean_toggle.css'),)}
        js = (static('js/boolean_toggle.js'),)


class ChainedLocationWidget(forms.Widget):

    class Media:
        js = ('js/location.js',)

    template_name = None

    def get_context(self, name, value, attrs):

        selected_country = None
        selected_province = None
        selected_city = None

        provinces = []
        cities = []

        if value:
            try:
                city = City.objects.select_related(
                    'province__country'
                ).get(pk=value)

                selected_city = city
                selected_province = city.province
                selected_country = city.province.country

                provinces = Province.objects.filter(
                    country=selected_country
                )

                cities = City.objects.filter(
                    province=selected_province
                )

            except City.DoesNotExist:
                pass

        return {
            'name': name,
            'countries': Country.objects.all(),

            'selected_country': selected_country,
            'selected_province': selected_province,
            'selected_city': selected_city,

            'provinces': provinces,
            'cities': cities,

            'province_url': reverse('get_provinces'),
            'city_url': reverse('get_cities'),
        }

    def render(self, name, value, attrs=None, renderer=None):

        context = self.get_context(name, value, attrs)

        html = """
            <div class="chained-location-widget">
            <div class="form-group mb-3">
                <select id="id_country" class="form-control" data-url="{province_url}">
                    <option value="">کشور را انتخاب نمایید</option>
                    {country_options}
                </select>
            </div>

            <div class="form-group mb-3">
                <select id="id_province" class="form-control" data-url="{city_url}" {province_disabled}>
                    <option value="">استان را انتخاب نمایید</option>
                    {province_options}
                </select>
            </div>

            <div class="form-group mb-3">
                <select id="id_city"
                        name="{name}"
                        class="form-control"
                        {city_disabled}>
                    <option value="">شهر محل سکونت را انتخاب نمایید</option>
                    {city_options}
                </select>
            </div>
        </div>
        """

        country_options = ''.join([
            f'''
            <option value="{country.id}"
            {"selected" if context["selected_country"] and context["selected_country"].id == country.id else ""}>
                {country.name}
            </option>
            '''
            for country in context['countries']
        ])

        province_options = ''.join([
            f'''
            <option value="{province.id}"
            {"selected" if context["selected_province"] and context["selected_province"].id == province.id else ""}>
                {province.name}
            </option>
            '''
            for province in context['provinces']
        ])

        city_options = ''.join([
            f'''
            <option value="{city.id}"
            {"selected" if context["selected_city"] and context["selected_city"].id == city.id else ""}>
                {city.name}
            </option>
            '''
            for city in context['cities']
        ])

        return mark_safe(
            html.format(
                name=context['name'],
                province_url=context['province_url'],
                city_url=context['city_url'],
                country_options=country_options,
                province_options=province_options,
                city_options=city_options,
                province_disabled='' if context['selected_country'] else 'disabled',
                city_disabled='' if context['selected_province'] else 'disabled'
            )
        )

    def value_from_datadict(self, data, files, name):
        return data.get(name)
    

class UsernameInput(forms.TextInput):
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control text-center',
            'maxlength': '10',
            'minlength': '10',
            'inputmode': 'numeric',  # کیبورد عددی در موبایل
            'pattern': '[0-9]{10}',  # برای اعتبارسنجی HTML5
        }
        if attrs:
            default_attrs.update(attrs)

        super().__init__(attrs=default_attrs)

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.setdefault('oninput', "this.value = this.value.replace(/[^0-9]/g, '')")
        attrs.setdefault('onkeypress', "return event.charCode >= 48 && event.charCode <= 57")
        return attrs

    class Media:
        js = (
            static('js/input-rules.js'),
        )


class ChainedStudyWidget(forms.Widget):

    class Media:
        js = ('js/study.js',)

    def get_context(self, name, value, attrs):

        selected_field = None
        selected_specialization = None

        specializations = []

        if value:
            try:
                specialization = Specialization.objects.select_related(
                    "field"
                ).get(pk=value)

                selected_specialization = specialization
                selected_field = specialization.field

                specializations = Specialization.objects.filter(
                    field=selected_field
                )

            except Specialization.DoesNotExist:
                pass

        return {
            "name": name,
            "fields": FieldOfStudy.objects.all(),

            "selected_field": selected_field,
            "selected_specialization": selected_specialization,

            "specializations": specializations,

            "specialization_url": reverse("get_specializations"),
        }

    def render(self, name, value, attrs=None, renderer=None):

        context = self.get_context(name, value, attrs)

        html = """
        <div class="chained-specialization-widget">

            <div class="form-group mb-3">
                <select id="id_field"
                        class="form-control"
                        data-url="{specialization_url}">

                    <option value="">رشته را انتخاب نمایید</option>

                    {field_options}

                </select>
            </div>

            <div class="form-group mb-3">
                <select id="id_specialization"
                        name="{name}"
                        class="form-control"
                        {disabled}>

                    <option value="">گرایش را انتخاب نمایید</option>

                    {specialization_options}

                </select>
            </div>

        </div>
        """

        field_options = "".join([
            f"""
            <option value="{field.id}"
            {"selected" if context["selected_field"] and context["selected_field"].id == field.id else ""}>
                {field.name}
            </option>
            """
            for field in context["fields"]
        ])

        specialization_options = "".join([
            f"""
            <option value="{specialization.id}"
            {"selected" if context["selected_specialization"] and context["selected_specialization"].id == specialization.id else ""}>
                {specialization.name}
            </option>
            """
            for specialization in context["specializations"]
        ])

        return mark_safe(
            html.format(
                name=context["name"],
                specialization_url=context["specialization_url"],
                field_options=field_options,
                specialization_options=specialization_options,
                disabled="" if context["selected_field"] else "disabled",
            )
        )

    def value_from_datadict(self, data, files, name):
        return data.get(name)
    


class GPAWidget(forms.Widget):

    class Media:
        js = ('js/gpa.js',)

    def get_context(self, name, value, attrs):

        return {
            "name": name,
            "value": value if value is not None else "",
        }

    def render(self, name, value, attrs=None, renderer=None):

        context = self.get_context(name, value, attrs)

        html = """
        <div class="gpa-widget">

            <div class="input-group">

                <input
                    id="id_{name}"
                    name="{name}"
                    type="number"
                    class="form-control"
                    min="0"
                    max="20"
                    step="0.01"
                    value="{value}"
                    placeholder="مثلاً 18.75">

               
                <button type="button"  class="btn " style="background:#527093;color:#fff;" disabled="" data-bs-toggle="button">از 20 </button>

            </div>

            <div id="id_{name}_status"
                 class="small mt-2 text-muted">
               معدل را به صورت عدد به همراه نقطه وارد کنید
            </div>

        </div>
        """

        return mark_safe(
            html.format(
                name=context["name"],
                value=context["value"],
            )
        )

    def value_from_datadict(self, data, files, name):
        return data.get(name)
    


class CustomTextWidget(forms.TextInput):

    class Media:
        js = ('js/input-rules.js',)

    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control',
            'data-input-type': 'persian-letters', 
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)