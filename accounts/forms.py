from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField
from django.contrib.auth import password_validation
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import Profile
import re

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label=_('ایمیل'),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ایمیل خود را وارد کنید',
            'autocomplete': 'email',
            'required': True
        })
    )
    
    phone_number = forms.CharField(
        label=_('شماره موبایل'),
        max_length=15,
        min_length=11,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '09xxxxxxxxx',
            'pattern': r'^09[0-9]{9}$',
            'autocomplete': 'tel',
            'required': True
        }),
        help_text=_('شماره موبایل باید با 09 شروع شود')
    )
    
    date_of_birth = forms.DateField(
        label=_('تاریخ تولد'),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'max': timezone.now().date().strftime('%Y-%m-%d'),
            'required': True
        })
    )
    

    class Meta:
        model = Profile
        fields = ('username', 'email', 'phone_number', 'date_of_birth', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Labels فارسی
        self.fields['username'].label = _('نام کاربری')
        self.fields['password1'].label = _('رمز عبور')
        self.fields['password2'].label = _('تکرار رمز عبور')
        
        # Help texts فارسی
        self.fields['password1'].help_text = password_validation.password_validators_help_text_html()
        self.fields['password2'].help_text = _('برای تأیید، رمز عبور را دوباره وارد کنید.')
        
        # Styling
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'نام کاربری',
            'autocomplete': 'username'
        })

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone and not re.match(r'^09[0-9]{9}$', phone):
            raise forms.ValidationError(_('شماره موبایل باید با 09 شروع شود و 11 رقم باشد.'))
        if Profile.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError(_('این شماره قبلاً استفاده شده است.'))
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Profile.objects.filter(email=email).exists():
            raise forms.ValidationError(_('این ایمیل قبلاً استفاده شده است.'))
        return email

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
    email = forms.EmailField(
        label=_('ایمیل'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ایمیل خود را وارد کنید'
        })
    )
    
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

    class Meta:
        model = Profile
        fields = ('username', 'email', 'phone_number', 'date_of_birth',)
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام کاربری'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Labels فارسی
        for field in self.fields:
            self.fields[field].label = {
                'username': 'نام کاربری',
                'email': 'ایمیل',
                'phone_number': 'شماره موبایل',
                'date_of_birth': 'تاریخ تولد',
            }.get(field, field.title())

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone and Profile.objects.filter(phone_number=phone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_('این شماره قبلاً استفاده شده است.'))
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and Profile.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_('این ایمیل قبلاً استفاده شده است.'))
        return email