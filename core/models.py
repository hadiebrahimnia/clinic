from django.db import models
from accounts.models import Profile
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from django.utils import timezone
from django.conf import settings

class Logs(models.Model):
    ACTION_CHOICES = [
        ('create', 'ایجاد'),
        ('update', 'ویرایش'),
        ('delete', 'حذف'),

    ]

    profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=('کاربر انجام‌دهنده'))
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name=('نوع عملیات'))
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name=('نوع مدل'))
    object_id = models.PositiveIntegerField(verbose_name=('شناسه شیء'))
    changed_object = GenericForeignKey('content_type', 'object_id')  # برای اشاره به مدل تغییر یافته (مانند Turn یا Plan)
    changes = models.JSONField(null=True, blank=True, verbose_name=('جزئیات تغییرات'))  # ذخیره تغییرات به صورت JSON
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=('زمان'))

    class Meta:
        verbose_name = ('تاریخچه')
        verbose_name_plural = ('تاریخچه')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.content_type} در {self.action} توسط {self.profile} در {self.timestamp}"
    







# FEATURES = {
#     'basic': {
#         'appointment_booking': True,
#         'specialist_profile': True,
#         'patient_management': True,
#         'tests_basic': True,
#         'reports': False,
#         'sms_notification': False,
#         'multi_branch': False,
#     },
#     'professional': {
#         'appointment_booking': True,
#         'specialist_profile': True,
#         'patient_management': True,
#         'tests_basic': True,
#         'tests_advanced': True,
#         'reports': True,
#         'sms_notification': True,
#         'multi_branch': False,
#     },
#     'premium': {
#         'appointment_booking': True,
#         'specialist_profile': True,
#         'patient_management': True,
#         'tests_basic': True,
#         'tests_advanced': True,
#         'reports': True,
#         'sms_notification': True,
#         'multi_branch': True,
#         'custom_branding': True,
#     }
# }

# def get_user_features(subscription):
#     if not subscription or not subscription.is_active:
#         return FEATURES.get('basic', {})
    
#     return FEATURES.get(subscription.plan_type, FEATURES['basic'])


# class Feature(models.Model):
#     name = models.CharField(max_length=100, unique=True) 
#     display_name = models.CharField(max_length=200)
#     description = models.TextField(blank=True)

# class Subscription(models.Model):
#     features = models.ManyToManyField(Feature, blank=True)


# class Subscription(models.Model):
#     clinic = models.ForeignKey(
#         'clinic.Clinic',
#         on_delete=models.CASCADE,
#         related_name='subscription'
#     )

#     PLAN_CHOICES = [
#         ('basic', 'پایه'),
#         ('professional', 'حرفه‌ای'),
#         ('premium', 'پرمیوم'),
#         ('enterprise', 'سازمانی'),
#     ]
#     plan_type = models.CharField(
#         max_length=20,
#         choices=PLAN_CHOICES,
#         default='basic'
#     )

#     features = models.JSONField(default=dict, blank=True)

#     STATUS_CHOICES = [
#         ('trial', 'دوره آزمایشی'),
#         ('active', 'فعال'),
#         ('expired', 'منقضی شده'),
#         ('cancelled', 'لغو شده'),
#         ('suspended', 'تعلیق شده'),
#     ]
#     status = models.CharField(
#         max_length=15,
#         choices=STATUS_CHOICES,
#         default='trial'
#     )
    
#     starts_at = models.DateField()                    # تاریخ شروع اجرا
#     expires_at = models.DateField()                   # تاریخ انقضا
#     trial_ends_at = models.DateField(null=True, blank=True)
    
#     last_payment_id = models.CharField(max_length=100, null=True, blank=True)
#     last_payment_at = models.DateTimeField(null=True, blank=True)
    
#     cancelled_at = models.DateTimeField(null=True, blank=True)
#     cancelled_reason = models.TextField(null=True, blank=True)
    
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         verbose_name = "اشتراک"
#         verbose_name_plural = "اشتراک‌ها"
#         ordering = ['-created_at']
#         indexes = [
#             models.Index(fields=['clinic']),
#             models.Index(fields=['status']),
#             models.Index(fields=['expires_at']),
#         ]

#     def __str__(self):
#         return f"{self.clinic.name} - {self.get_plan_type_display()} ({self.get_status_display()})"

#     @property
#     def is_active(self) -> bool:
#         """بررسی اینکه اشتراک فعال است یا خیر"""
#         if self.status == 'active' and self.expires_at >= timezone.now().date():
#             return True
#         return False

#     @property
#     def is_trial(self) -> bool:
#         """بررسی دوره آزمایشی"""
#         if self.status == 'trial' and self.trial_ends_at and self.trial_ends_at >= timezone.now().date():
#             return True
#         return False

#     @property
#     def is_expired(self) -> bool:
#         return self.expires_at < timezone.now().date()

