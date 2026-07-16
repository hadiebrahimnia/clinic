from django.db import models
from accounts.models import *
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Questionnaire(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان پرسشنامه")
    name_fa = models.CharField(max_length=200, verbose_name="نام",blank=True, null=True,)
    name_en = models.CharField(max_length=200, verbose_name="Name",blank=True, null=True,)
    cost = models.PositiveIntegerField(blank=True, null=True, verbose_name="هزینه",default=0)
    question = models.PositiveIntegerField(blank=True, null=True, verbose_name="تعداد سوالات",default=0)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد")
    is_active = models.BooleanField(default=False,verbose_name="وضعیت فعالیت")
    is_deleted = models.BooleanField(default=False,verbose_name="حذف شده")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    def __str__(self):
        return self.title


# ویژگی
class Attribute(models.Model):
    name_en = models.CharField(max_length=100)
    name_fa = models.CharField(max_length=100,blank=True,null=True,)
    is_active = models.BooleanField(default=False,verbose_name="وضعیت فعالیت")
    is_deleted = models.BooleanField(default=False,verbose_name="حذف شده")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.title


# سوالات
class Question(models.Model):
    QUESTION_TYPES = [
        ('MC', 'چندگزینه‌ای'),
        ('TX', 'متن آزاد'),
        ('SC', 'مقیاس (مثل لیکرت)'),
    ]
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='questions')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='questions')  # اصلاح: related_name correct شد (قبلاً 'ویژگی' اشتباه بود)
    text = models.TextField(verbose_name="متن سؤال")
    question_type = models.CharField(max_length=2, choices=QUESTION_TYPES, verbose_name="نوع سؤال")
    order = models.PositiveIntegerField(default=1, verbose_name="ترتیب نمایش")
    required = models.BooleanField(default=True, verbose_name="اجباری")

    is_active = models.BooleanField(default=False,verbose_name="وضعیت فعالیت")
    is_deleted = models.BooleanField(default=False,verbose_name="حذف شده")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.text[:50]}..."


# گزینه ها
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=200, verbose_name="متن گزینه")
    value = models.IntegerField(default=0, verbose_name="ارزش عددی (برای امتیازدهی)")
    is_active = models.BooleanField(default=False,verbose_name="وضعیت فعالیت")
    is_deleted = models.BooleanField(default=False,verbose_name="حذف شده")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.text


# آزمون
class Response(models.Model):
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='responses')
    respondent = models.ForeignKey(
        Profile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="پاسخ‌دهنده"
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان شروع")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان تکمیل")
    is_completed = models.BooleanField(default=False, verbose_name="تکمیل شده")
    is_active = models.BooleanField(default=False,verbose_name="وضعیت فعالیت")
    is_deleted = models.BooleanField(default=False,verbose_name="حذف شده")
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"پاسخ به {self.questionnaire.title} توسط {self.respondent or 'ناشناس'}"


# جواب
class Answer(models.Model):
    response = models.ForeignKey(
        Response,
        on_delete=models.CASCADE,  # مهم: با حذف Response، تمام Answerها حذف شوند
        related_name='answers'
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True)
    text_answer = models.TextField(blank=True, verbose_name="پاسخ متنی")
    scale_value = models.IntegerField(null=True, blank=True, verbose_name="ارزش مقیاس")
    RT = models.PositiveIntegerField(null=True, blank=True, verbose_name="زمان پاسخ‌دهی (ثانیه)")
    is_active = models.BooleanField(default=False,verbose_name="وضعیت فعالیت")
    is_deleted = models.BooleanField(default=False,verbose_name="حذف شده")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"جواب به {self.question.text[:20]}..."


# نتیجه
class Result(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name="کاربر")
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, verbose_name="آزمون")
    response = models.ForeignKey(
        Response,
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name="Response"
    )
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, verbose_name="Attribute")
    num_questions = models.IntegerField(verbose_name="تعداد سوالات مربوط به ویژگی", default=0)
    raw_score = models.FloatField(verbose_name="نمره خام", default=0.0)
    average_score = models.FloatField(verbose_name="میانگین نمره", default=0.0)
    sum_rt = models.PositiveIntegerField(verbose_name="جمع RT", default=0)
    average_rt = models.FloatField(verbose_name="میانگین RT", default=0.0)

    is_active = models.BooleanField(default=False,verbose_name="وضعیت فعالیت")
    is_deleted = models.BooleanField(default=False,verbose_name="حذف شده")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        unique_together = ('response', 'attribute')
        constraints = [
            models.UniqueConstraint(fields=['response', 'attribute'], name='unique_response_attribute')
        ]

    def __str__(self):
        return f"نتیجه {self.attribute.title} برای {self.user.username} در {self.questionnaire.title}"
    
class Test(models.Model):
    title = models.CharField(max_length=255)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    is_active = models.BooleanField(default=False,verbose_name="وضعیت فعالیت")
    is_deleted = models.BooleanField(default=False,verbose_name="حذف شده")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
