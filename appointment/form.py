from django import forms
from core.widget import *
from .models import *


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