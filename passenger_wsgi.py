import os
import sys

# مسیر پروژه خود را مشخص کنید
sys.path.insert(0, os.path.dirname(__file__))

# تنظیم متغیر محیطی Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic.settings')

# وارد کردن application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()