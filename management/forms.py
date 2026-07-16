from django import forms
from accounts.models import *
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from core.widget import *

class RoleForm(forms.ModelForm):
    name = forms.CharField(
        label='نقش', 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نقش'
        })
    )
    class Meta:
        model = Role
        fields = ['name']


class CountryForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = ['name', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control text-center', 'required': True}),
            'icon': forms.TextInput(attrs={'class': 'form-control text-center', 'required': False}),
        }


class ProvinceForm(forms.ModelForm):
    class Meta:
        model = Province
        fields = ['name', 'country']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control text-center', 'required': True}),
            'country': forms.Select(attrs={'class': 'form-control text-center', 'required': True}),
        }


class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ['name', 'province']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control text-center', 'required': True}),
            'province': forms.Select(attrs={'class': 'form-control text-center', 'required': True}),
        }


class SpecialtyForm(forms.ModelForm):
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
        fields = ['name', 'background_color', 'color', 'icon', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control text-center', 'required': True}),
            'background_color': forms.TextInput(attrs={'class': 'form-control text-center', 'required': False, 'type': 'color'}),
            'color': forms.TextInput(attrs={'class': 'form-control text-center', 'required': False, 'type': 'color'}),
        }


class UniversityForm(forms.ModelForm):
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
        model = University
        fields = ['name', 'city', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control text-center', 'required': True}),
            'city': forms.Select(attrs={'class': 'form-control text-center', 'required': False}),
        }


class FieldOfStudyForm(forms.ModelForm):
    description = forms.CharField(
        label="توضیحات",
        required=False,
        widget=CKEditorUploadingWidget(
            config_name='default'
        )
    )
    class Meta:
        model = FieldOfStudy
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control text-center', 'required': True}),
        }


class SpecializationForm(forms.ModelForm):
    class Meta:
        model = Specialization
        fields = ['name', 'field']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control text-center', 'required': True}),
            'field': forms.Select(attrs={'class': 'form-control text-center', 'required': True}),
        }


class PsychologistTypeForm(forms.ModelForm):
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
        fields = ['name', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control text-center', 'required': True}),
        }


class SectionTypeForm(forms.ModelForm):
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
        fields = ['title', 'icon']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control text-center', 'required': True}),
            'icon': forms.ClearableFileInput(attrs={'class': 'form-control text-center'}),
        }


class PlatformForm(forms.ModelForm):
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
        fields = ['title', 'url', 'icon']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control text-center', 'required': True}),
            'url': forms.TextInput(attrs={'class': 'form-control text-center', 'required': False}),
        }