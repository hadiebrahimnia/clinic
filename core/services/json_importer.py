import json

from django.apps import apps
from django.db import transaction

import json
from django.apps import apps
from django.db import transaction
from django.db.models import ForeignKey

class JsonImporter:

    @transaction.atomic
    def run(self, model_path, json_file):
        app_label, model_name = model_path.split(".")
        model = apps.get_model(app_label, model_name)

        data = json.load(json_file)

        if not isinstance(data, list):
            raise Exception("فرمت فایل باید آرایه باشد.")

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
        processed = []
        meta = model._meta
        fk_fields = {field.name: field for field in meta.get_fields() 
                    if isinstance(field, ForeignKey)}

        for row in data:
            new_row = row.copy()

            for field_name, field in fk_fields.items():
                if f"{field_name}_id" in new_row:
                    continue

                name_key = None
                possible_keys = [f"{field_name}Name", f"{field_name}_name", field_name, 
                               f"{field.target_field.model.__name__}Name"]
                
                for key in possible_keys:
                    if key in new_row and str(new_row.get(key)).strip():
                        name_key = key
                        break

                if name_key:
                    related_value = str(new_row.pop(name_key)).strip()
                    related_model = field.related_model

                    try:
                        # جستجوی مقاوم‌تر برای فارسی
                        related_obj = self._get_related_object(related_model, related_value)
                        new_row[field_name] = related_obj
                    except related_model.DoesNotExist:
                        raise Exception(
                            f"{related_model.__name__} با نام '{related_value}' پیدا نشد.\n"
                            f"لطفاً ابتدا کشور را وارد کنید."
                        )

            processed.append(new_row)

        return processed

    def _get_related_object(self, model, value):
        """جستجوی قوی برای اشیاء مرتبط (به خصوص فارسی)"""
        value = value.strip()
        
        # روش ۱: دقیق
        try:
            return model.objects.get(name=value)
        except model.DoesNotExist:
            pass

        # روش ۲: case-insensitive + strip
        try:
            return model.objects.get(name__iexact=value)
        except model.DoesNotExist:
            pass

        # روش ۳: حذف فاصله‌های اضافی و جستجو
        normalized = ' '.join(value.split())
        try:
            return model.objects.get(name__iexact=normalized)
        except model.DoesNotExist:
            pass

        # روش ۴: جستجو با contains (آخرین چاره)
        objs = model.objects.filter(name__icontains=normalized)
        if objs.exists():
            return objs.first()

        raise model.DoesNotExist()

    def _get_unique_lookup(self, model, row):
        meta = model._meta

        for constraint in meta.constraints:
            if hasattr(constraint, 'fields') and all(f in row for f in constraint.fields):
                return {f: row[f] for f in constraint.fields}

        if meta.unique_together:
            for fields_tuple in meta.unique_together:
                if all(f in row for f in fields_tuple):
                    return {f: row[f] for f in fields_tuple}

        if 'name' in row:
            return {'name': row['name']}

        return {list(row.keys())[0]: row[list(row.keys())[0]]}