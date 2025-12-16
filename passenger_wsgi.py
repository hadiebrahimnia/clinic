import os
import sys

# اضافه کردن مسیر پروژه به sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# تنظیم متغیر محیطی Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic.settings')

# گرفتن WSGI application از Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()