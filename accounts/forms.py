from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField
from django.contrib.auth import password_validation
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import Profile
import re
from core.widget import *

class CustomUserCreationForm(UserCreationForm):
    
    phone_number = forms.CharField(
        label=_('شماره موبایل'),
        max_length=15,
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
        fields = ('username', 'phone_number', 'date_of_birth', 'password1', 'password2')
        
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
    username = UsernameField(
         label=_('کد ملی'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'کد ملی',
            'autocomplete': 'username',
            'autofocus': True
        })
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

class ProfileUpdateForm(forms.ModelForm):
    
    phone_number = forms.CharField(
        label=_('شماره موبایل'),
        max_length=15,
        min_length=11,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '09xxxxxxxxx',
            'pattern': r'^09[0-9]{9}$'
        })
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
    class Meta:
        model = Profile
        fields = ('username', 'phone_number', 'date_of_birth',)
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


        
        # Labels فارسی
        for field in self.fields:
            self.fields[field].label = {
                'username': 'کدملی',
                'phone_number': 'شماره موبایل',
                'date_of_birth': 'تاریخ تولد',
            }.get(field, field.title())

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone and Profile.objects.filter(phone_number=phone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_('این شماره قبلاً استفاده شده است.'))
        return phone

