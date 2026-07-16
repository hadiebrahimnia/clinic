from django import forms
from accounts.models import *
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from core.widget import *

class RoleForm(forms.ModelForm):
    name_en = forms.CharField(
        label='نام به انگلیسی', 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به انگلیسی'
        })
    )
    name_fa = forms.CharField(
        label='نام به فارسی', 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به فارسی'
        })
    )
    
    class Meta:
        model = Role
        fields = ['name_en','name_fa']


class CountryForm(forms.ModelForm):
    name_fa = forms.CharField(
        label='نام به فارسی', 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به فارسی'
        })
    )
    name_en = forms.CharField(
        label='نام به انگلیسی', 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به انگلیسی'
        })
    )
    icon = forms.CharField(
        label='آیکون', 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'آیکون'
        })
    )
    class Meta:
        model = Country
        fields = ['name_fa','name_en','icon']
        


class ProvinceForm(forms.ModelForm):
    name_fa = forms.CharField(
        label='نام به فارسی', 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به فارسی'
        })
    )
    name_en = forms.CharField(
        label='نام به انگلیسی', 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به انگلیسی'
        })
    )
    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        required=True,
        empty_label="کشور را انتخاب کنید",
        label="عنوان فعالیت",
        widget=ForeignKeySearchWidget(
            placeholder="کشور را انتخاب کنید",
        )
    )   

    class Meta:
        model = Province
        fields = ['name_fa', 'name_en','country']
        


class CityForm(forms.ModelForm):
    name_fa = forms.CharField(
        label='نام به فارسی', 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به فارسی'
        })
    )
    name_en = forms.CharField(
        label='نام به انگلیسی', 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به انگلیسی'
        })
    )
    province = forms.ModelChoiceField(
        queryset=Province.objects.all(),
        required=True,
        empty_label="استان را انتخاب کنید",
        label="عنوان فعالیت",
        widget=ForeignKeySearchWidget(
            placeholder="استان را انتخاب کنید",
        )
    )   
    class Meta:
        model = City
        fields = ['name_fa','name_en' ,'province']
        


class SpecialtyForm(forms.ModelForm):
    name_fa = forms.CharField(
        label='نام به فارسی', 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به فارسی'
        })
    )
    name_en = forms.CharField(
        label='نام به انگلیسی', 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به انگلیسی'
        })
    )

    icon = forms.ImageField(
        required=False,
        label="عکس/آیکون",
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
            config_name='default'
        )
    )
    class Meta:
        model = Specialty
        fields = ['name_fa','name_en', 'background_color', 'color', 'icon', 'description']
        widgets = {
            'background_color': forms.TextInput(attrs={'class': 'form-control text-center', 'required': False, 'type': 'color'}),
            'color': forms.TextInput(attrs={'class': 'form-control text-center', 'required': False, 'type': 'color'}),
        }

class UniversityForm(forms.ModelForm):
    name_fa = forms.CharField(
        label='نام به فارسی', 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به فارسی'
        })
    )
    name_en = forms.CharField(
        label='نام به انگلیسی', 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به انگلیسی'
        })
    )
    type = forms.ChoiceField(
        label='نوع دانشگاه', 
        required=False,
        choices=[('', 'نوع دانشگاه')] + list(TYPE_UNIVERSITY),
        widget=forms.Select(attrs={'class': 'form-control text-center', 'required': False})
    )

    link = forms.CharField(
        label='لینک سایت', 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder':'لینک سایت',
        })
    )

    phone = forms.CharField(
        label='شماره تلفن', 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder':'شماره تلفن',
        })
    )

    address = forms.CharField(
        label='آدرس', 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder':'آدرس',
        })
    )

    email = forms.CharField(
        label='لینک سایت', 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder':'ایمیل',
        })
    )

    city = forms.ModelChoiceField(
        queryset=City.objects.all(),
        required=False,
        empty_label="شهر را انتخاب کنید",
        label="عنوان فعالیت",
        widget=ForeignKeySearchWidget(
            placeholder="شهر را انتخاب کنید",
        )
    )  

    icon = forms.ImageField(
        required=False,
        label="عکس/آیکون",
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
            config_name='default'
        )
    )
    class Meta:
        model = University
        fields = ['name_fa','name_en','type','link','phone','address','email', 'city', 'icon','description']

class FieldOfStudyForm(forms.ModelForm):
    name_fa = forms.CharField(
        label='نام به فارسی', 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به فارسی'
        })
    )
    name_en = forms.CharField(
        label='نام به انگلیسی', 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به انگلیسی'
        })
    )
    description = forms.CharField(
        label="توضیحات",
        required=False,
        widget=CKEditorUploadingWidget(
            config_name='default'
        )
    )
    class Meta:
        model = FieldOfStudy
        fields = ['name_fa','name_en', 'description']
        


class SpecializationForm(forms.ModelForm):
    name_fa = forms.CharField(
        label='نام به فارسی', 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به فارسی'
        })
    )
    name_en = forms.CharField(
        label='نام به انگلیسی', 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به انگلیسی'
        })
    )
    field = forms.ModelChoiceField(
        queryset=FieldOfStudy.objects.all(),
        required=True,
        empty_label="رشته را انتخاب کنید",
        label="عنوان فعالیت",
        widget=ForeignKeySearchWidget(
            placeholder="رشته را انتخاب کنید",
        )
    )   

    class Meta:
        model = Specialization
        fields = ['name_fa','name_en', 'field']
        


class PsychologistTypeForm(forms.ModelForm):
    name_fa = forms.CharField(
        label='نام به فارسی', 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به فارسی'
        })
    )
    name_en = forms.CharField(
        label='نام به انگلیسی', 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به انگلیسی'
        })
    )
    icon = forms.ImageField(
        required=False,
        label="عکس/آیکون",
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
            config_name='default'
        )
    )
    class Meta:
        model = PsychologistType
        fields = ['name_fa','name_en', 'icon', 'description']
        

class SectionTypeForm(forms.ModelForm):
    name_fa = forms.CharField(
        label='نام به فارسی', 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به فارسی'
        })
    )
    name_en = forms.CharField(
        label='نام به انگلیسی', 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به انگلیسی'
        })
    )
    icon = forms.ImageField(
        required=False,
        label="عکس/آیکون",
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
        model = SectionType
        fields = ['name_fa','name_en', 'icon']
        

class PlatformForm(forms.ModelForm):
    name_fa = forms.CharField(
        label='نام به فارسی', 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به فارسی'
        })
    )
    name_en = forms.CharField(
        label='نام به انگلیسی', 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'به انگلیسی'
        })
    )

    url = forms.CharField(
        label='پیشوند آدرس', 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'پیشوند آدرس'
        })
    )

    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        required=False,
        empty_label="کشور را انتخاب کنید",
        label="کشور سازنده",
        widget=ForeignKeySearchWidget(
            placeholder="کشور را انتخاب کنید",
        )
    )   

    icon = forms.ImageField(
        required=False,
        label="عکس/آیکون",
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
        model = Platform
        fields = ['name_fa','name_en','country','url','icon']
        