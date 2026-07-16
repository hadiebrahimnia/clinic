from django.apps import apps
from django.db import transaction
from django.db.models import ForeignKey
import json
from hazm import Normalizer
from accounts.models import *

class JsonImporter:
    
    def __init__(self):
        self.normalizer = Normalizer()   # فقط یک بار ساخته شود

    def _normalize_persian(self, text):
        """نرمال‌سازی متن فارسی با استفاده از Hazm"""
        if not isinstance(text, str):
            return text
        # حذف فاصله‌های اضافی + نرمال‌سازی کامل فارسی
        return self.normalizer.normalize(text.strip())

    @transaction.atomic
    def run(self, model_path, json_file):
        app_label, model_name = model_path.split(".")
        model = apps.get_model(app_label, model_name)
        
        data = json.load(json_file)
        
        if not isinstance(data, list):
            raise Exception("فرمت فایل باید آرایه (list) باشد.")
        
        processed_data = self._preprocess_data(model, data)
        
        created_count = 0
        updated_count = 0
        
        for row in processed_data:
            try:
                obj, created = model.objects.update_or_create(
                    **self._get_unique_lookup(model, row),
                    defaults=row
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                raise Exception(f"خطا در پردازش ردیف:\n{row}\n\nجزئیات: {str(e)}")
        
        return f"{created_count} رکورد جدید | {updated_count} رکورد بروزرسانی شد."

    def _preprocess_data(self, model, data):
        """پیش‌پردازش داده‌ها + نرمال‌سازی فارسی"""
        processed = []
        meta = model._meta
        fk_fields = {
            field.name: field 
            for field in meta.get_fields() 
            if isinstance(field, ForeignKey)
        }
        
        for row in data:
            # کپی ردیف
            new_row = row.copy()
            
            # === نرمال‌سازی همه مقادیر رشته‌ای ===
            for key, value in list(new_row.items()):
                if isinstance(value, str):
                    new_row[key] = self._normalize_persian(value)
            
            # === پردازش ForeignKeyها ===
            for field_name, field in fk_fields.items():
                if f"{field_name}_id" in new_row:
                    continue
                    
                name_key = None
                print(field_name)
                possible_keys = [
                    f"{field_name}Name",
                    f"{field_name}_name",
                    f"{field_name}_name_fa",
                    f"{field_name}_name_en",
                    f"{field_name}Name_fa",
                    f"{field_name}Name_Fa",
                    f"{field_name}Name_en",
                    f"{field_name}Name_En",
                    field_name,
                    f"{field.related_model.__name__}Name",
                    f"{field.related_model.__name__}_name",
                    f"{field.related_model.__name__}_name_fa",
                    f"{field.related_model.__name__}_Name_Fa",
                    f"{field.related_model.__name__}_name_en",
                    f"{field.related_model.__name__}_Name_en",
                     f"{field.related_model.__name__}_Name_En",
                ]
                
                for key in possible_keys:
                    if key in new_row and str(new_row.get(key)).strip():
                        name_key = key
                        break
                        
                if name_key:
                    related_value = new_row.pop(name_key)
                    related_model = field.related_model
                    
                    try:
                        related_obj = self._get_related_object(related_model, related_value)
                        new_row[field_name] = related_obj
                    except related_model.DoesNotExist:
                        raise Exception(
                            f"{related_model.__name__} با نام '{related_value}' پیدا نشد.\n"
                            f"لطفاً ابتدا {related_model.__name__} را وارد کنید."
                        )
            
            processed.append(new_row)
        
        return processed

    def _get_related_object(self, model, value):

        """جستجوی قوی با نرمال‌سازی فارسی"""
        try:
            us=Country.objects.filter(name_fa="ایالات متحده آمریکا").exists()
        except:
            us="dont"

        print(us)

        if not isinstance(value, str):
            value = str(value)

        normalized = self._normalize_persian(value)

        # فیلدهای احتمالی نام
        name_fields = [
            "name",
            "name_fa",
        ]

        for field_name in name_fields:

            # بررسی اینکه فیلد واقعاً در مدل وجود دارد
            try:
                model._meta.get_field(field_name)
            except Exception:
                continue

            # جستجوی دقیق
            obj = model.objects.filter(
                **{field_name: normalized}
            ).first()

            if obj:
                return obj

            # جستجوی بدون حساسیت به حروف
            obj = model.objects.filter(
                **{f"{field_name}__iexact": normalized}
            ).first()

            if obj:
                return obj

            # جستجوی تقریبی
            obj = model.objects.filter(
                **{f"{field_name}__icontains": normalized}
            ).first()

            if obj:
                return obj

        raise model.DoesNotExist(
            f"«{value}» پیدا نشد "
            f"(نرمال‌شده: {normalized})"
        )

    def _get_unique_lookup(self, model, row):
        """تشخیص کلید یکتا برای update_or_create"""
        meta = model._meta
        
        # بررسی constraints
        for constraint in meta.constraints:
            if hasattr(constraint, 'fields') and all(f in row for f in constraint.fields):
                return {f: row[f] for f in constraint.fields}
        
        # unique_together
        if meta.unique_together:
            for fields_tuple in meta.unique_together:
                if all(f in row for f in fields_tuple):
                    return {f: row[f] for f in fields_tuple}
        
        # اگر فیلد name داشت
        if 'name' in row:
            return {'name': row['name']}
        
        # fallback
        first_key = list(row.keys())[0]
        return {first_key: row[first_key]}