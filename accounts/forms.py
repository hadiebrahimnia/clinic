from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField
from django.contrib.auth import password_validation
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import *
import re
from core.widget import *
from core.validators import validate_image
from ckeditor_uploader.widgets import CKEditorUploadingWidget

class CustomUserCreationForm(UserCreationForm):
    
    phone_number = forms.CharField(
        label=_('شماره موبایل'),
        max_length=11,
        min_length=11,
        widget=PersianPhoneInput(attrs={
            'class': 'form-control',
            'placeholder': 'شماره موبایل',
            'required': True
        }),
    )
    
    date_of_birth = forms.DateField(
        label=_('تاریخ تولد'),
        widget=PersianDateInput(attrs={
            'class': 'form-control text-center date',
            'placeholder': 'تاریخ تولد',
            'data-jdp-max-date': 'today',
            'required': True
        }),
    )

    gender = forms.ChoiceField(
        label=_('جنسیت'),
        choices=[('', 'جنسیت را انتخاب نمایید')] + list(Profile.GENDER_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-control text-center',
            'required': True
        })
    )
    
    password1 = forms.CharField(
        label=_("رمز عبور"),
        widget=PasswordStrengthInput()  # اصلی: قوانین + progress + چشم
    )
    password2 = forms.CharField(
        label=_("تکرار رمز عبور"),
        widget=PasswordStrengthInput(is_confirm=True)  # فقط نشانگر تطابق + چشم
    )

    class Meta:
        model = Profile
        fields = ('username', 'phone_number', 'date_of_birth','gender', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Labels فارسی
        self.fields['username'].label = _('کدملی')
        self.fields['username'].help_text = None
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
        
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'کدملی',
            'autocomplete': 'username'
        })

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone and not re.match(r'^09[0-9]{9}$', phone):
            raise forms.ValidationError(_('شماره موبایل باید با 09 شروع شود و 11 رقم باشد.'))
        if Profile.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError(_('این شماره قبلاً استفاده شده است.'))
        return phone


class CustomAuthenticationForm(AuthenticationForm):
    
    username = forms.CharField(
        label=_('کدملی'),
        max_length=10,
        min_length=10,
        widget=UsernameInput(attrs={
            'class': 'form-control',
            'placeholder': 'کدملی',
            'data-input-type': 'number',
            'required': True
        }),
    )
    
    password = forms.CharField(
        label=_('رمز عبور'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور',
            'autocomplete': 'current-password'
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

        self.fields['username'].max_length = 10
        self.fields['username'].widget.attrs['maxlength'] = 10
        self.fields['username'].widget.attrs['minlength'] = 10


class ProfileUpdateForm(forms.ModelForm):

    phone_number = forms.CharField(
        label=_('شماره موبایل'),
        max_length=11,
        min_length=11,
        
        widget=PersianPhoneInput(attrs={
            'class': 'form-control',
            'placeholder': 'شماره موبایل',
            'data-input-type': 'number',
            'required': True
        }),
    )
    
    date_of_birth = forms.DateField(
        label=_('تاریخ تولد'),
        widget=PersianDateInput(attrs={
            'class': 'form-control text-center date',
            'placeholder': 'تاریخ تولد',
            'data-jdp-max-date': 'today',
            'required': True
        }),
    )

    gender = forms.ChoiceField(
        label=_('جنسیت'),
        choices=[('', 'جنسیت را انتخاب نمایید')] + list(Profile.GENDER_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-control text-center',
            'required': True
        })
    )

    city = forms.ModelChoiceField(
        queryset=City.objects.all().select_related('province__country'),
        label='شهر محل سکونت',
        required=True,
        widget=ChainedLocationWidget()
    )

    class Meta:
        model = Profile
        fields = ('username', 'phone_number', 'date_of_birth','gender','city')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'کدملی'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = None
        if self.instance and self.instance.pk and getattr(self.instance, 'city', None):
            self.fields['city'].initial = self.instance.city.pk

        
        # Labels فارسی
        for field in self.fields:
            self.fields[field].label = {
                'username': 'کدملی',
                'phone_number': 'شماره موبایل',
                'date_of_birth': 'تاریخ تولد',
                'gender': 'جنسیت',
                'city': 'محل سکونت',
            }.get(field, field.title())

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone and Profile.objects.filter(phone_number=phone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_('این شماره قبلاً استفاده شده است.'))
        return phone


class PsychologistCreationUpdateForm(forms.ModelForm):

    first_name = forms.CharField(
        label=_('نام'),
        widget=CustomTextWidget(attrs={
            'class': 'form-control',
            'placeholder': 'نام',
            'data-input-type': 'persian-letters',
            'required': True,
        }),
    )

    last_name = forms.CharField(
        label=_('نام خانوادگی'),
        widget=CustomTextWidget(attrs={
            'class': 'form-control',
            'placeholder': 'نام خانوادگی',
            'data-input-type': 'persian-letters',
            'required': True,
        }),
    )
    
    PsychologistType = forms.ModelChoiceField(
        queryset=PsychologistType.objects.all(),
        required=True,
        empty_label="عنوان فعالیت را انتخاب کنید",
        label="عنوان فعالیت",
        widget=ForeignKeySearchWidget(
            placeholder="عنوان فعالیت را انتخاب کنید",
        )
    )   

    profile_picture = forms.ImageField(
        required=True,
        label="عکس پروفایل",
        widget=ImageInput(
            allowed_formats=['jpg', 'jpeg', 'png'],
            max_size_mb=1,
            min_width=200,
            min_height=200,
            max_width=1800,
            max_height=1800,
        )
    ) 

    hire_date = forms.DateField(
        label=_('تاریخ استخدام/شروع فعالیت'),
        required=False,
        widget=PersianDateInput(attrs={
            'class': 'form-control text-center date',
            'placeholder': 'تاریخ استخدام/شروع فعالیت',
            'data-jdp-max-date': 'today',
            'required': False
        }),
    )

    class Meta:
        model = Psychologist
        
        fields = [
            'first_name',
            'last_name',
            'PsychologistType',
            'profile_picture',
            'hire_date',
        ]

    def __init__(self, *args, **kwargs):
        self.request = None        
        if args and hasattr(args[0], 'user'):     
            self.request = args[0]
            args = args[1:]
        else:
            self.request = kwargs.pop('request', None)

        super().__init__(*args, **kwargs)

        # مقداردهی اولیه در حالت ویرایش
        instance = kwargs.get('instance')
        if instance and instance.profile:
            self.fields['first_name'].initial = instance.profile.first_name
            self.fields['last_name'].initial = instance.profile.last_name

        self.order_fields(['first_name', 'last_name', 'PsychologistType', 'profile_picture','hire_date'])

    def clean(self):
        cleaned_data = super().clean()

        for field_name, field in self.fields.items():
            if isinstance(field.widget, ImageInput):
                image = cleaned_data.get(field_name)
                if image:
                    attrs = field.widget.attrs
                    allowed_formats = attrs.get('data-allowed-formats', 'jpg,jpeg,png').split(',')
                    max_size_mb = float(attrs.get('data-max-size', 2))
                    min_width = int(attrs.get('data-min-width', 0))
                    min_height = int(attrs.get('data-min-height', 0))
                    max_width = int(attrs.get('data-max-width', 10000))
                    max_height = int(attrs.get('data-max-height', 10000))

                    try:
                        validate_image(
                            image,
                            allowed_formats=allowed_formats,
                            max_size_mb=max_size_mb,
                            min_width=min_width,
                            min_height=min_height,
                            max_width=max_width,
                            max_height=max_height,
                        )
                    except forms.ValidationError as e:
                        self.add_error(field_name, e)

        return cleaned_data
    
    def save(self, commit=True):
        psychologist = super().save(commit=False)

        profile = self.request.user
        profile.first_name = self.cleaned_data['first_name']
        profile.last_name = self.cleaned_data['last_name']

        profile.save()   # همیشه ذخیره شود

        psychologist.profile = profile

        if commit:
            psychologist.save()

        return psychologist

class PsychologistSpecialtieForm(forms.ModelForm):
    
    specialties = forms.ModelMultipleChoiceField(
        queryset=Specialty.objects.all(),
        required=True,
        label="زمینه کاری",
        widget=ManyToManySearchWidget(
            placeholder="زمینه کاری را انتخاب کنید",
        )
    )  

    class Meta:
        model = PsychologistSpecialtie
        fields = ['specialties']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # اختیاری: مرتب‌سازی یا فیلتر queryset
        self.fields['specialties'].queryset = Specialty.objects.all().order_by('name')
        

class PsychologistDegreeForm(forms.ModelForm):
    level = forms.ChoiceField(
        label='مقطع تحصیلی',
        choices=[('', 'مقطع تحصیلی را انتخاب نمایید')] + list(PsychologistDegree.DEGREE_LEVELS),
        widget=forms.Select(attrs={'class': 'form-control text-center', 'required': True})
    )
    study_status = forms.ChoiceField(
        label='وضعیت',
        choices=[('', 'وضعیت این مقطع را انتخاب نمایید')] + list(PsychologistDegree.STUDY_STATUS),
        widget=forms.Select(attrs={'class': 'form-control text-center', 'required': True})
    )

    specialization = forms.ModelChoiceField(
        queryset=Specialization.objects.all().select_related('field'),
        label='رشته',
        required=True,
        widget=ChainedStudyWidget()
    )

    university = forms.ModelChoiceField(
        queryset=University.objects.all(),
        required=True,
        empty_label="دانشگاه محل تحصیل را انتخاب کنید",
        label="دانشگاه",
        widget=ForeignKeySearchWidget(placeholder="دانشگاه محل تحصیل را انتخاب کنید")
    )

    start_year = forms.DateField(
        label='تاریخ شروع',
        widget=PersianDateInput(attrs={
            'class': 'form-control text-center date',
            'placeholder': 'تاریخ شروع تحصیل',
            'data-jdp-max-date': 'today',
            'required': True
        })
    )

    graduation_year = forms.DateField(
        label='تاریخ پایان',
        widget=PersianDateInput(attrs={
            'class': 'form-control text-center date',
            'placeholder': 'تاریخ پایان تحصیل',
            'required': True
        })
    )
    gpa = forms.DecimalField(
        label='معدل',
        required=False,
        widget=DecimalWidget(
            min_value=0,
            max_value=20,
            placeholder='بافرمت **.**',
            help_text='عدد به همراه نقطه'
        )
    )
    
    thesis_title = forms.CharField(
        label='عنوان پایان‌نامه',
        required=False,
        widget=CustomTextWidget(attrs={'class': 'form-control', 'placeholder': 'عنوان پایان نامه'})
    )

    degree_file = forms.ImageField(
        label="تصویر مدرک",
        required=True,
        widget=ImageInput(
            allowed_formats=['jpg', 'jpeg', 'png'],
            max_size_mb=1,
            min_width=200,
            min_height=200,
            max_width=1800,
            max_height=1800,
        )
    )

    class Meta:
        model = PsychologistDegree
        fields = [
            'level', 'specialization', 'university', 'start_year',
            'graduation_year', 'study_status', 'gpa', 'thesis_title', 'degree_file'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.order_fields([
            "level", 
            "specialization",
            "university", 
            "start_year", 
            "graduation_year",
            "study_status", 
            "gpa",
            "thesis_title", 
            "degree_file",
        ])

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance
    

class PsychologistDocumentForm(forms.ModelForm):

    document_type = forms.ChoiceField(
        label='نوع سند',
        choices=[('', 'نوع سند را انتخاب نمایید')] + list(PsychologistDocument.DOCUMENT_TYPES),
        widget=forms.Select(attrs={'class': 'form-control text-center', 'required': True})
    )
    
    title = forms.CharField(
        label=_('عنوان سند'),
        required=False,
        widget=CustomTextWidget(attrs={
            'class': 'form-control',
            'placeholder': 'عنوان سند',
            'data-input-type': 'all',
            'required': False,
        }),
    )

    code = forms.CharField(
        label=_('کد/شماره'),
        required=False,
        widget=CustomTextWidget(attrs={
            'class': 'form-control',
            'placeholder': 'کد / شماره سند وارد نمایید',
            'data-input-type': 'all',
            'required': False,
        }),
    )

    document_image = forms.ImageField(
        label="تصویر مدرک",
        required=True,
        widget=ImageInput(
            allowed_formats=['jpg', 'jpeg', 'png'],
            max_size_mb=1,
            min_width=200,
            min_height=200,
            max_width=1800,
            max_height=1800,
        )
    )

    description = forms.CharField(
        label="توضیحات",
        required=False,
        widget=CKEditorUploadingWidget(
            config_name='PsychologistDocument'
        )
    )

    class Meta:
        model = PsychologistDocument
        fields = [
            "document_type",
            "title",
            "code",
            "document_image",
            "description",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.order_fields([
            "level", 

        ])

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance



class PsychologistSectionForm(forms.ModelForm):

    section_type = forms.ModelChoiceField(
        queryset=SectionType.objects.all(),
        required=True,
        empty_label="عنوان را انتخاب کنید",
        label="عنوان",
        widget=ForeignKeySearchWidget(
            placeholder="عنوان را انتخاب کنید",
        )
    )  


    description = forms.CharField(
        label="توضیحات",
        required=False,
        widget=CKEditorUploadingWidget(
            config_name='PsychologistDocument'
        )
    )

    order = forms.DecimalField(
        label='رتبه',
        required=False,
        widget=DecimalWidget(
            min_value=1,
            max_value=1000,
            step=1,
            placeholder='ترتیب نمایش در صفحه معرفی',
        )
    )

    background_color = forms.CharField(
        label="رنگ زمینه",
        widget=ColorWidget(help_text='رنگ زمینه'),
        initial="#ffffff",          # ← اینجا مقدار پیش‌فرض
    )

    color = forms.CharField(
        label="رنگ متن",
        widget=ColorWidget(help_text='رنگ متن'),
        initial="#282f53",          # ← اینجا مقدار پیش‌فرض
    )

    class Meta:
        model = PsychologistSection
        fields = [
            "section_type",
            "description",
            "order",
            "background_color",
            "color",
           
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.order_fields([
            "level", 

        ])

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance
    


class PsychologistSocialMediaForm(forms.ModelForm):
    
    platform = forms.ModelChoiceField(
        queryset=Platform.objects.all(),
        required=True,
        empty_label="اپلیکشن را انتخاب کنید",
        label="اپلیکشن",
        widget=ForeignKeySearchWidget(
            placeholder="اپلیکشن را انتخاب کنید",
        )
    )  
    
    url = forms.CharField(
        label='آدرس کاربری', 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'آدرس کاربری'
        })
    )

    class Meta:
        model = PsychologistSocialMedia
        fields = [
            "platform",
            "url",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.order_fields([
            "platform", 
            "url",
        ])

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance
    

class SecretaryCreationUpdateForm(forms.ModelForm):

    first_name = forms.CharField(
        label=_('نام'),
        widget=CustomTextWidget(attrs={
            'class': 'form-control',
            'placeholder': 'نام',
            'data-input-type': 'persian-letters',
            'required': True,
        }),
    )

    last_name = forms.CharField(
        label=_('نام خانوادگی'),
        widget=CustomTextWidget(attrs={
            'class': 'form-control',
            'placeholder': 'نام خانوادگی',
            'data-input-type': 'persian-letters',
            'required': True,
        }),
    )
    

    profile_picture = forms.ImageField(
        required=True,
        label="عکس پروفایل",
        widget=ImageInput(
            allowed_formats=['jpg', 'jpeg', 'png'],
            max_size_mb=1,
            min_width=200,
            min_height=200,
            max_width=1800,
            max_height=1800,
        )
    ) 

    employee_code = forms.CharField(
        label=_('کد عضویت / پرسنلی'),
        required=False,
        widget=CustomTextWidget(attrs={
            'class': 'form-control',
            'placeholder': 'کد عضویت / پرسنلی',
            'data-input-type': 'number',
            'required': False,
        }),
    )

    hire_date = forms.DateField(
        label=_('تاریخ استخدام/شروع فعالیت'),
        required=False,
        widget=PersianDateInput(attrs={
            'class': 'form-control text-center date',
            'placeholder': 'تاریخ استخدام/شروع فعالیت',
            'data-jdp-max-date': 'today',
            'required': False
        }),
    )

    class Meta:
        model = Secretary
        
        fields = [
            'first_name',
            'last_name',
            'profile_picture',
            'employee_code',
            'hire_date',
        ]

    def __init__(self, *args, **kwargs):
        self.request = None        
        if args and hasattr(args[0], 'user'):     
            self.request = args[0]
            args = args[1:]
        else:
            self.request = kwargs.pop('request', None)

        super().__init__(*args, **kwargs)

        # مقداردهی اولیه در حالت ویرایش
        instance = kwargs.get('instance')
        if instance and instance.profile:
            self.fields['first_name'].initial = instance.profile.first_name
            self.fields['last_name'].initial = instance.profile.last_name

        self.order_fields(['first_name', 'last_name', 'profile_picture','employee_code','hire_date'])

    def clean(self):
        cleaned_data = super().clean()

        for field_name, field in self.fields.items():
            if isinstance(field.widget, ImageInput):
                image = cleaned_data.get(field_name)
                if image:
                    attrs = field.widget.attrs
                    allowed_formats = attrs.get('data-allowed-formats', 'jpg,jpeg,png').split(',')
                    max_size_mb = float(attrs.get('data-max-size', 2))
                    min_width = int(attrs.get('data-min-width', 0))
                    min_height = int(attrs.get('data-min-height', 0))
                    max_width = int(attrs.get('data-max-width', 10000))
                    max_height = int(attrs.get('data-max-height', 10000))

                    try:
                        validate_image(
                            image,
                            allowed_formats=allowed_formats,
                            max_size_mb=max_size_mb,
                            min_width=min_width,
                            min_height=min_height,
                            max_width=max_width,
                            max_height=max_height,
                        )
                    except forms.ValidationError as e:
                        self.add_error(field_name, e)

        return cleaned_data
    
    def save(self, commit=True):
        secretary = super().save(commit=False)

        profile = self.request.user
        profile.first_name = self.cleaned_data['first_name']
        profile.last_name = self.cleaned_data['last_name']

        profile.save()   # همیشه ذخیره شود

        secretary.profile = profile

        if commit:
            secretary.save()

        return secretary
