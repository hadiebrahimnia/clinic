"""
passenger_wsgi.py — فایل صحیح برای اجرای Django با Phusion Passenger در cPanel
"""

import os
import sys

# ------------------- مسیر پروژه را به sys.path اضافه کن -------------------
# این خط خیلی مهم است — بدون آن Django پیدا نمی‌شود
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

# ------------------- فعال‌سازی virtualenv (اختیاری اما توصیه می‌شود) -------------------
# اگر cPanel خودش virtualenv را مدیریت می‌کند، این بخش را می‌توانی کامنت کنی
# اما اگر مشکلی داشتی، این بخش را فعال کن
# VIRTUAL_ENV = '/home/erfancli/virtualenv/repositories/clinic/3.11'  # نسخه پایتون را درست بنویس
# activate_this = os.path.join(VIRTUAL_ENV, 'bin', 'activate_this.py')
# if os.path.exists(activate_this):
#     exec(open(activate_this).read(), dict(__file__=activate_this))

# ------------------- تنظیمات Django -------------------
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic.settings')  # clinic نام پروژه‌ات است

# اگر در پروداکشن DEBUG=False باشد، این خط باعث می‌شود ارورهای حساس نشان داده نشود
# os.environ['DJANGO_DEBUG'] = 'False'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()