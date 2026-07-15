from django.db import models
from datetime import timedelta
from accounts.models import *


class Room(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=False,verbose_name="وضعیت فعالیت")
    is_deleted = models.BooleanField(default=False,verbose_name="حذف شده")


    def __str__(self):
        return self.name
    
class SessionType(models.TextChoices):
    IN_PERSON = "IN_PERSON", "حضوری"
    ONLINE = "ONLINE", "آنلاین"
    PHONE = "PHONE", "تلفنی"


class WeekDay(models.IntegerChoices):
    SATURDAY = 0, "شنبه"
    SUNDAY = 1, "یکشنبه"
    MONDAY = 2, "دوشنبه"
    TUESDAY = 3, "سه شنبه"
    WEDNESDAY = 4, "چهارشنبه"
    THURSDAY = 5, "پنجشنبه"
    FRIDAY = 6, "جمعه"

class PsychologistNewPatients(models.Model):
    psychologist = models.ForeignKey(
        'accounts.Psychologist',
        on_delete=models.CASCADE,
        related_name='new_patients'
    )
    is_accepting_new_patients = models.BooleanField(default=False,verbose_name="مراجع جدید")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class WorkSchedule(models.Model):

    psychologist = models.ForeignKey(
        Psychologist,
        on_delete=models.CASCADE,
        related_name="work_schedules",
        verbose_name="متخصص"
    )

    weekday = models.IntegerField(
        choices=WeekDay.choices,
        verbose_name="روز هفته"
    )

    start_time = models.TimeField(
        verbose_name="ساعت شروع"
    )

    end_time = models.TimeField(
        verbose_name="ساعت پایان"
    )

    session_type = models.CharField(
        max_length=20,
        choices=SessionType.choices,
        verbose_name="نوع جلسه"
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="work_schedules",
        verbose_name="اتاق"
    )

    session_duration = models.PositiveIntegerField(
        default=45,
        verbose_name="مدت جلسه (دقیقه)"
    )

    break_duration = models.PositiveIntegerField(
        default=15,
        verbose_name="استراحت بین جلسات (دقیقه)"
    )

    price = models.PositiveIntegerField(
        verbose_name="هزینه جلسه"
    )

    allowed_roles = models.ManyToManyField(
        Role,
        blank=True,
        related_name="work_schedules",
        verbose_name="نقش‌های مجاز"
    )

    booking_days_ahead = models.PositiveIntegerField(
        default=30,
        verbose_name="نمایش نوبت تا چند روز آینده"
    )

    minimum_booking_hours = models.PositiveIntegerField(
        default=2,
        verbose_name="حداقل زمان رزرو قبل از جلسه (ساعت)"
    )

    cancel_before_hours = models.PositiveIntegerField(
        default=24,
        verbose_name="مهلت لغو نوبت (ساعت)"
    )

    require_confirmation = models.BooleanField(
        default=False,
        verbose_name="نیاز به تأیید رزرو"
    )

    effective_from = models.DateField(
        null=True,
        blank=True,
        verbose_name="اعتبار از تاریخ"
    )

    effective_to = models.DateField(
        null=True,
        blank=True,
        verbose_name="اعتبار تا تاریخ"
    )

    is_active = models.BooleanField(
        default=False,
        verbose_name="فعال"
    )

    is_deleted = models.BooleanField(
        default=False,
        verbose_name="حذف شده"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["weekday", "start_time"]
        verbose_name = "WorkSchedule"
        verbose_name_plural = "WorkSchedule"

    def __str__(self):
        return f"{self.psychologist} | {self.get_weekday_display()} | {self.start_time}-{self.end_time}"
    

class Appointment(models.Model):

    schedule = models.ForeignKey(
        WorkSchedule,
        on_delete=models.PROTECT,
        related_name="appointments"
    )

    psychologist = models.ForeignKey(
        Psychologist,
        on_delete=models.PROTECT
    )
    
    patient = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    )

    date = models.DateField()
    start_time = models.TimeField()
    session_duration = models.PositiveIntegerField()
    end_time = models.TimeField()

    session_type = models.CharField(
        max_length=20,
        choices=SessionType.choices
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    price = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "در انتظار"),
            ("confirmed", "تایید شده"),
            ("done", "انجام شده"),
            ("cancelled", "لغو شده"),
        ],
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)
