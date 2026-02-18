from django.core.exceptions import ValidationError
from PIL import Image

def validate_image(file, *, allowed_formats, max_size_mb, min_width, min_height, max_width, max_height):
    allowed_formats = [f.lower() for f in allowed_formats]
    file_ext = file.name.split('.')[-1].lower()

    # بررسی حجم
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'حجم فایل نباید بیشتر از {max_size_mb} مگابایت باشد.')

    # بررسی فرمت
    if file_ext not in allowed_formats:
        raise ValidationError(f'فرمت مجاز: {", ".join(allowed_formats)}')

    # بررسی ابعاد
    try:
        img = Image.open(file)
        width, height = img.size
    except Exception:
        raise ValidationError('فایل انتخابی یک تصویر معتبر نیست.')

    if width < min_width or height < min_height:
        raise ValidationError(f'حداقل ابعاد باید {min_width}×{min_height}px باشد.')
    if width > max_width or height > max_height:
        raise ValidationError(f'حداکثر ابعاد {max_width}×{max_height}px است.')

    return file
