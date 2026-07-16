from django import forms
from core.widget import *
from .models import *
from ckeditor_uploader.widgets import CKEditorUploadingWidget


class PsychologistNewPatientsForm(forms.ModelForm):
    
    is_accepting_new_patients = forms.BooleanField(
        required=False,
        initial=True,
        label="آیا مراجع جدید می‌پذیرید؟",
        widget=BooleanToggleWidget(
            label_true="بله، می‌پذیرم",
            label_false="خیر، فعلاً نمی‌پذیرم",
            color_true="#09ad95", 
            color_false="#e82646",
        )
    )

    class Meta:
        model = PsychologistNewPatients
        fields = ['is_accepting_new_patients']



class RoomForm(forms.ModelForm):
    description = forms.CharField(
        label="توضیحات",
        required=False,
        widget=CKEditorUploadingWidget(
            config_name='default'
        )
    )
    class Meta:
        model = Room
        fields = ['name', 'code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={ 'class': 'form-control text-center', 'required': True }), 
            'code': forms.TextInput(attrs={ 'class': 'form-control text-center', 'required': True }),            
        }


class SessionTypeForm(forms.ModelForm):
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
        model = SessionType
        fields = ['name', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={ 'class': 'form-control text-center', 'required': True }), 

        }