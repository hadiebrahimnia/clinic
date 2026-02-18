from django.db import models
from accounts.models import Profile
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


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
