from django.contrib.auth.models import AbstractUser
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django.utils.text import slugify
from ckeditor_uploader.fields import RichTextUploadingField


class Role(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=2, blank=True,null=True,)

    def __str__(self):
        return self.name

class Province(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='provinces')

    class Meta:
        unique_together = ['name', 'country']  # جلوگیری از تکرار نام استان در یک کشور

    def __str__(self):
        return f"{self.name}, {self.country}"

class City(models.Model):
    name = models.CharField(max_length=100)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='cities')

    class Meta:
        unique_together = ['name', 'province']  # جلوگیری از تکرار نام شهر در یک استان

    def __str__(self):
        return f"{self.name}, {self.province}"
    
class Specialty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = RichTextUploadingField(blank=True ,null=True,)
    icon = models.ImageField(
        upload_to='Specialty/icons/',
        blank=True,
        null=True,
        verbose_name="آیکون",
        help_text="آیکون کوچک برای نمایش در فیلترها (مثلاً 64x64)"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "تخصص ها"
        verbose_name_plural = "Specialties"

class University(models.Model):
    name = models.CharField(max_length=200, unique=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='universities')
    icon = models.ImageField(
        upload_to='University/icons/',
        blank=True,
        null=True,
        verbose_name="آیکون",
        help_text="آیکون کوچک برای نمایش در فیلترها (مثلاً 64x64)"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "University"
        verbose_name_plural = "Universities"

class FieldOfStudy(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = RichTextUploadingField(blank=True,null=True,)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "رشته تحصیلی"
        verbose_name_plural = "Fields of Study"

class Specialization(models.Model):
    name = models.CharField(max_length=100)
    field = models.ForeignKey(FieldOfStudy, on_delete=models.CASCADE, related_name='specializations')

    class Meta:
        unique_together = ['name', 'field']
        verbose_name = "گرایش تحصیلی"
        verbose_name_plural = "Specializations"

    def __str__(self):
        return f"{self.name} ({self.field})"

class Profile(AbstractUser):
    phone_number = models.CharField(max_length=11, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    GENDER_CHOICES = (
        ('M', 'مرد'),
        ('F', 'زن'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, blank=True, null=True, related_name='residents')

    roles = models.ManyToManyField(
        Role,
        blank=True,
        related_name='users',
        verbose_name='نقش‌ها'
    )

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set', 
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    ACCESS_LEVELS = (
        ('basic', 'پایه'),
        ('readonly', 'فقط خواندنی'),
        ('editor', 'ویرایشگر'),
        ('advanced', 'پیشرفته'),
    )

    access_level = models.CharField(
        max_length=20,
        choices=ACCESS_LEVELS,
        default='basic',
        verbose_name="سطح دسترسی کلی"
    )

    def __str__(self):
        return self.username
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "User"
    
    @property
    def is_profile_complete(self):
        """بررسی اینکه آیا اطلاعات پایه پروفایل تکمیل شده است"""
        return all([
            bool(self.phone_number),
            bool(self.date_of_birth),
            bool(self.gender),
            bool(self.city),
        ])
    
class Secretary(models.Model):
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name='secretary'
    )

    profile_picture = models.ImageField(
        upload_to='images/Secretary/profiles',
        blank=True, null=True,
        verbose_name="عکس پروفایل",
    )
    
    employee_code = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    hire_date = models.DateField(blank=True,null=True)
    is_active = models.BooleanField(default=False,verbose_name="وضعیت فعالیت")
    is_deleted = models.BooleanField(default=False,verbose_name="حذف شده")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.profile.get_full_name() or self.profile.username

class PsychologistType(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="نام نوع متخصص"
    )
    description = RichTextUploadingField(blank=True,null=True,)
    icon = models.ImageField(
        upload_to='psychologist_types/icons/',
        blank=True,
        null=True,
        verbose_name="آیکون",
        help_text="آیکون کوچک برای نمایش در فیلترها (مثلاً 64x64)"
    )

    def __str__(self):
        return self.name

class Psychologist(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='psychologist')
    PsychologistType = models.ForeignKey(PsychologistType, on_delete=models.CASCADE, related_name='PsychologistType',null=True,blank=True)
    profile_picture = models.ImageField(
        upload_to='images/psychologists/profiles',
        blank=True, null=True,
        verbose_name="عکس پروفایل",
    )
    hire_date = models.DateField(blank=True,null=True)
    is_active = models.BooleanField(default=False,verbose_name="وضعیت فعالیت")
    is_deleted = models.BooleanField(default=False,verbose_name="حذف شده")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dr. {self.profile.username}"

    class Meta:
        verbose_name = "متخصص"
        verbose_name_plural = "Psychologists"

class PsychologistDocument(models.Model):
    DOCUMENT_TYPES = [
        ('membership_card', 'عضویت'),
        ('license_card', 'پروانه اشتغال'),
        ('certificate', 'گواهینامه'),
        ('other', 'سایر'),
    ]

    psychologist = models.ForeignKey(
        'Psychologist', 
        on_delete=models.CASCADE,
        related_name='documents'
    )
    
    document_type = models.CharField(
        max_length=50, 
        choices=DOCUMENT_TYPES,
        verbose_name="نوع سند"
    )
    
    document_image = models.ImageField(
        upload_to='images/psychologists/documents/',
        verbose_name="تصویر سند"
    )
    
    title = models.CharField(max_length=200, blank=True, verbose_name="عنوان")
    code = models.CharField(max_length=200, blank=True, verbose_name="کد")
    description = RichTextUploadingField(blank=True,null=True,)

    is_active = models.BooleanField(default=False,verbose_name="وضعیت فعالیت")
    is_deleted = models.BooleanField(default=False,verbose_name="حذف شده")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ====================== کنترل نمایش آیتم ها   ======================
    display_config = models.JSONField(
        default=dict,
        blank=True,
    )
    CONTROLLABLE_FIELDS = [
        'document_type',
        'document_image',
        'title',
        'code',
        'description',
    ]
    def is_visible(self, field_name: str) -> bool:
        return self.display_config.get(field_name, False)
    def toggle_visibility(self, field_name: str):
        current = self.display_config.get(field_name, False)
        self.display_config[field_name] = not current
        self.save(update_fields=['display_config'])
        return self.display_config[field_name]
    # ====================== مقداردهی اولیه ======================
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and not self.display_config:
            self.display_config = {field: False for field in self.CONTROLLABLE_FIELDS}
        for field in self.CONTROLLABLE_FIELDS:
            if field not in self.display_config:
                self.display_config[field] = False
        super().save(*args, **kwargs)
    # متد کمکی (اختیاری)
    def reset_display_config(self):
        """اگر بعداً خواستی همه را ریست کنی"""
        self.display_config = {field: False for field in self.CONTROLLABLE_FIELDS}
        self.save(update_fields=['display_config'])
    # ====================== کنترل نمایش آیتم ها   ======================

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.psychologist}"


class PsychologistSpecialties(models.Model):
    psychologist = models.ForeignKey(
        'Psychologist',
        on_delete=models.CASCADE,
        related_name='specialties'
    )
    specialties = models.ManyToManyField(Specialty,verbose_name="زمینه کاری", related_name='psychologists', blank=True)
    
    is_active = models.BooleanField(default=False,verbose_name="وضعیت فعالیت")
    is_deleted = models.BooleanField(default=False,verbose_name="حذف شده")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PsychologistDegree(models.Model):
    psychologist = models.ForeignKey(
        'Psychologist',
        on_delete=models.CASCADE,
        related_name='degrees'
    )

    DEGREE_LEVELS = (
        ('Associate', 'کاردانی'),
        ('Bachelor', 'کارشناسی'),
        ('Master', 'کارشناسی ارشد'),
        ('PhD', 'دکتری'),
        ('PostDoc', 'پسادکتری'),
    )

    STUDY_STATUS = (
        ('Studying', 'در حال تحصیل'),
        ('Graduated', 'فارغ‌التحصیل'),
        ('Dropped', 'انصراف داده'),
    )

    level = models.CharField(
        max_length=9,
        choices=DEGREE_LEVELS
    )

    specialization = models.ForeignKey(
        Specialization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='degrees'
    )

    university = models.ForeignKey(
        University,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='degrees'
    )

    start_year = models.DateField(
        blank=True,
        null=True,
        verbose_name="تاریخ شروع تحصیل"
    )

    graduation_year = models.DateField(
        blank=True,
        null=True,
        verbose_name="تاریخ پایان تحصیل"
    )

    study_status = models.CharField(
        max_length=20,
        choices=STUDY_STATUS,
        default='graduated',
        verbose_name="وضعیت تحصیل"
    )

    gpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="معدل"
    )

    thesis_title = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="عنوان پایان‌نامه"
    )

    degree_file = models.FileField(
        upload_to='degrees/',
        blank=True,
        null=True,
        verbose_name="فایل مدرک"
    )

    is_active = models.BooleanField(default=False,verbose_name="وضعیت فعالیت")
    is_deleted = models.BooleanField(default=False,verbose_name="حذف شده")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    order = models.PositiveIntegerField(
        default=0
    )
    # ====================== کنترل نمایش آیتم ها   ======================
    display_config = models.JSONField(
        default=dict,
        blank=True,
    )
    CONTROLLABLE_FIELDS = [
        'specialization',
        'university',
        'start_year',
        'graduation_year',
        'gpa',
        'thesis_title',
        'degree_file',
    ]
    def is_visible(self, field_name: str) -> bool:
        return self.display_config.get(field_name, False)
    def toggle_visibility(self, field_name: str):
        current = self.display_config.get(field_name, False)
        self.display_config[field_name] = not current
        self.save(update_fields=['display_config'])
        return self.display_config[field_name]
    # ====================== مقداردهی اولیه ======================
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and not self.display_config:
            self.display_config = {field: False for field in self.CONTROLLABLE_FIELDS}
        for field in self.CONTROLLABLE_FIELDS:
            if field not in self.display_config:
                self.display_config[field] = False
        super().save(*args, **kwargs)
    # متد کمکی (اختیاری)
    def reset_display_config(self):
        """اگر بعداً خواستی همه را ریست کنی"""
        self.display_config = {field: False for field in self.CONTROLLABLE_FIELDS}
        self.save(update_fields=['display_config'])
    # ====================== کنترل نمایش آیتم ها   ======================

    def __str__(self):
        return (
            f"{self.get_level_display()} "
            f"({self.specialization or 'N/A'})"
        )

# SECTION_TYPES = [
#         ('Biography', 'بیوگرافی'),
#         ('Books', 'کتاب‌ها'),
#         ('Publications', 'مقالات'),
#         ('Awards & Honors', 'جوایز و افتخارات'),
#         ('Associations & Memberships', 'انجمن ها و عضویت ها'),
#         ('Work Experience', 'تجربیات کاری'),
#         ('Therapeutic Approaches', 'رویکردهای درمانی'),
#         ('Disorders Treated', 'اختلا'),
#         ('Certifications', 'دوره ها  و گواهینامه '),
#         ('Educational Activities', 'فعالیت‌های آموزشی و تدریس'),
#         ('Research Activities', 'زفعالیت‌های پژوهشی'),
#          ('Supervision', 'سوپرویژن و نظارت بالینی'),
    # معرفی
    # تحصیلات
    # سوابق شغلی
    # حوزه‌های تخصص
    # خدمات
    # رویکردهای درمانی
    # مقالات و پژوهش‌ها
    # کتاب‌ها
    # دوره‌های آموزشی
    # کارگاه‌ها
    # افتخارات
    # گواهینامه‌ها
    # عضویت‌های حرفه‌ای
    # سوپرویژن و نظارت بالینی
    # پرسش‌های متداول
    # راه‌های ارتباطی
        
#     ]

class SectionType(models.Model):
    title = models.CharField(
        max_length=255,
        blank=True
    )
    icon = models.ImageField(
        upload_to='psychologist_types/icons/',
        blank=True,
        null=True,
        verbose_name="آیکون",
        help_text="آیکون کوچک برای نمایش در فیلترها (مثلاً 64x64)"
    )

    class Meta:
        verbose_name = "Section Type"
        verbose_name_plural = "Section Type Accounts"

    def __str__(self):
        return f"{self.title}"


class PsychologistSection(models.Model):
    psychologist = models.ForeignKey(
        Psychologist,
        on_delete=models.CASCADE,
        related_name='sections'
    )

    section_type = models.ForeignKey(
        SectionType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sections'
    )

    description = RichTextUploadingField(blank=True,null=True,)

    order = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
    )
    
    background_color = models.CharField(max_length=7, default="#ffffff", verbose_name="رنگ زمینه")
    color = models.CharField(max_length=7, default="#000000", verbose_name="رنگ متن")
    
    is_active = models.BooleanField(default=False,verbose_name="وضعیت فعالیت")
    is_deleted = models.BooleanField(default=False,verbose_name="حذف شده")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    # ====================== کنترل نمایش آیتم ها   ======================
    display_config = models.JSONField(
        default=dict,
        blank=True,
    )
    CONTROLLABLE_FIELDS = [
        'section_type',
        'description',
    ]
    def is_visible(self, field_name: str) -> bool:
        return self.display_config.get(field_name, False)
    def toggle_visibility(self, field_name: str):
        current = self.display_config.get(field_name, False)
        self.display_config[field_name] = not current
        self.save(update_fields=['display_config'])
        return self.display_config[field_name]
    # ====================== مقداردهی اولیه ======================
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and not self.display_config:
            self.display_config = {field: False for field in self.CONTROLLABLE_FIELDS}
        for field in self.CONTROLLABLE_FIELDS:
            if field not in self.display_config:
                self.display_config[field] = False
        super().save(*args, **kwargs)
    # متد کمکی (اختیاری)
    def reset_display_config(self):
        """اگر بعداً خواستی همه را ریست کنی"""
        self.display_config = {field: False for field in self.CONTROLLABLE_FIELDS}
        self.save(update_fields=['display_config'])
    # ====================== کنترل نمایش آیتم ها   ======================

    def __str__(self):
        return f"{self.psychologist} - {self.section_type}"
    

# PLATFORM_CHOICES = (
#         ('TW', 'Twitter/X'),
#         ('LI', 'LinkedIn'),
#         ('IG', 'Instagram'),
#         ('FB', 'Facebook'),
#         ('OT', 'Other'),
#     )

class Platform(models.Model):
    title = models.CharField(
        max_length=255,
        blank=True
    )
    url = models.CharField(
        max_length=100,
        verbose_name="پیشوند آدرس",
        null=True,
        blank=True,
    )
    icon = models.ImageField(
        upload_to='platform/icons/',
        blank=True,
        null=True,
        verbose_name="آیکون",
        help_text="آیکون کوچک برای نمایش در فیلترها (مثلاً 64x64)"
    )

    class Meta:
        verbose_name = "Platform"
        verbose_name_plural = "Platform"

    def __str__(self):
        return f"{self.title}"

class PsychologistSocialMedia(models.Model):
    psychologist = models.ForeignKey(
        Psychologist, 
        on_delete=models.CASCADE, 
        related_name='social_media'
    )
    platform = models.ForeignKey(
        Platform,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='social_media'
    )

    url = models.CharField(
        max_length=100,
        verbose_name="آدرس",
        null=True,
        blank=True,
    )
    
    is_active = models.BooleanField(default=False,verbose_name="وضعیت فعالیت")
    is_deleted = models.BooleanField(default=False,verbose_name="حذف شده")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ====================== کنترل نمایش آیتم ها   ======================
    display_config = models.JSONField(
        default=dict,
        blank=True,
    )
    CONTROLLABLE_FIELDS = [
        'platform',
        'url',
    ]
    def is_visible(self, field_name: str) -> bool:
        return self.display_config.get(field_name, False)
    def toggle_visibility(self, field_name: str):
        current = self.display_config.get(field_name, False)
        self.display_config[field_name] = not current
        self.save(update_fields=['display_config'])
        return self.display_config[field_name]
    # ====================== مقداردهی اولیه ======================
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and not self.display_config:
            self.display_config = {field: False for field in self.CONTROLLABLE_FIELDS}
        for field in self.CONTROLLABLE_FIELDS:
            if field not in self.display_config:
                self.display_config[field] = False
        super().save(*args, **kwargs)
    # متد کمکی (اختیاری)
    def reset_display_config(self):
        """اگر بعداً خواستی همه را ریست کنی"""
        self.display_config = {field: False for field in self.CONTROLLABLE_FIELDS}
        self.save(update_fields=['display_config'])
    # ====================== کنترل نمایش آیتم ها   ======================
    

    def __str__(self):
        return f"{self.psychologist}: {self.platform}"

    class Meta:
        verbose_name = "Social Media"
        verbose_name_plural = "Social Media"
