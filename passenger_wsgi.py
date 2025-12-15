import os
import sys

# تست: این خط یک فایل لاگ می‌سازه تا بفهمیم فایل اجرا شده یا نه
log_path = '/home/erfancli/test_passenger_load.txt'  # مسیر خانگی خودت
with open(log_path, 'a') as f:
    f.write('passenger_wsgi.py اجرا شد! زمان: ' + os.popen('date').read() + '\n')

# مسیر ریشه پروژه رو اضافه کن (مسیر کامل فولدر clinic)
PROJECT_DIR = '/home/erfancli/repositories/clinic'
sys.path.insert(0, PROJECT_DIR)

# تنظیمات Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic.settings')

# ایمپورت اپلیکیشن WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()