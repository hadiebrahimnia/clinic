from django import forms
from django.apps import apps
from core.widget import *

class JsonImportForm(forms.Form):
    model = forms.ChoiceField(
        label='مدل',
        widget=forms.Select(attrs={'class': 'form-control text-center', 'required': True})
    )
    json_file = forms.FileField(
        label="فایل JSON",
        widget=FileInput(
            allowed_extensions=["json"],
            max_size_mb=5,
            button_text="انتخاب فایل JSON"
        )
    )

    def __init__(self, *args, allowed_model=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if allowed_model:
            # فقط یک مدل خاص نمایش داده شود
            try:
                app_label, model_name = allowed_model.split('.')
                model = apps.get_model(app_label, model_name)
                choices = [(
                    f"{model._meta.app_label}.{model.__name__}",
                    f"{model._meta.app_label} / {model.__name__}"
                )]
            except Exception:
                choices = []
        else:
            # اگر allowed_model پاس نشد، همه مدل‌ها (رفتار قبلی)
            choices = [
                (f"{m._meta.app_label}.{m.__name__}", f"{m._meta.app_label} / {m.__name__}")
                for m in apps.get_models()
            ]

        self.fields["model"].choices = choices