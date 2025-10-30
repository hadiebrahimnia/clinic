from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import URLValidator


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)

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

class Profile(AbstractUser):
    phone_number = models.CharField(max_length=11, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    GENDER_CHOICES = (
        ('M', 'مرد'),
        ('F', 'زن'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, blank=True, null=True, related_name='residents')

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

    def __str__(self):
        return self.username
    
class University(models.Model):
    name = models.CharField(max_length=200, unique=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, related_name='universities')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "University"
        verbose_name_plural = "Universities"

# مدل برای رشته تحصیلی
class FieldOfStudy(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Field of Study"
        verbose_name_plural = "Fields of Study"

class Specialization(models.Model):
    name = models.CharField(max_length=100)
    field = models.ForeignKey(FieldOfStudy, on_delete=models.CASCADE, related_name='specializations')

    class Meta:
        unique_together = ['name', 'field']
        verbose_name = "Specialization"
        verbose_name_plural = "Specializations"

    def __str__(self):
        return f"{self.name} ({self.field})"

class Degree(models.Model):
    DEGREE_LEVELS = (
        ('B', 'Bachelor'),
        ('M', 'Master'),
        ('P', 'PhD'),
        ('O', 'Other'),
    )

    level = models.CharField(max_length=1, choices=DEGREE_LEVELS)
    field = models.ForeignKey(FieldOfStudy, on_delete=models.CASCADE, related_name='degrees')
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True, blank=True, related_name='degrees')
    university = models.ForeignKey(University, on_delete=models.SET_NULL, null=True, blank=True, related_name='degrees')
    graduation_year = models.PositiveIntegerField(blank=True, null=True)
    psychologist = models.ForeignKey('Psychologist', on_delete=models.CASCADE, related_name='degrees')

    def __str__(self):
        return f"{self.get_level_display()} in {self.field} ({self.specialization or 'N/A'}) - {self.university or 'Unknown'}"

    class Meta:
        verbose_name = "Degree"
        verbose_name_plural = "Degrees"

class Specialty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Specialty"
        verbose_name_plural = "Specialties"

class SocialMedia(models.Model):
    PLATFORM_CHOICES = (
        ('TW', 'Twitter/X'),
        ('LI', 'LinkedIn'),
        ('IG', 'Instagram'),
        ('FB', 'Facebook'),
        ('OT', 'Other'),
    )

    platform = models.CharField(max_length=2, choices=PLATFORM_CHOICES)
    url = models.URLField(validators=[URLValidator()])
    psychologist = models.ForeignKey('Psychologist', on_delete=models.CASCADE, related_name='social_media')

    def __str__(self):
        return f"{self.get_platform_display()}: {self.url}"

    class Meta:
        verbose_name = "Social Media"
        verbose_name_plural = "Social Media Accounts"

class Psychologist(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='psychologist')
    license_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    specialties = models.ManyToManyField(Specialty, related_name='psychologists', blank=True)
    is_accepting_new_patients = models.BooleanField(default=True)
    availability = models.TextField(
        blank=True, 
        null=True, 
        help_text="Availability details, e.g., days and hours of consultation"
    )
    languages_spoken = models.CharField(
        max_length=200, 
        blank=True, 
        null=True, 
        help_text="Comma-separated list of languages spoken by the psychologist"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dr. {self.profile.username} - {self.office_city or 'No city specified'}"

    class Meta:
        verbose_name = "Psychologist"
        verbose_name_plural = "Psychologists"