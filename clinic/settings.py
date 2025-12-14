# import pymysql
# pymysql.install_as_MySQLdb()
from pathlib import Path
import os

# مسیر اصلی پروژه
BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# تنظیمات امنیتی و هاست (برای پروداکشن)
# =============================================================================
SECRET_KEY = 'django-insecure-5kzj7q&y_69s7r^t9x+*5f9n_#&6a%j*%69o$je3lo(a1_40_k'  # حتماً بعد از دیپلوی عوض کن!

DEBUG = True

ALLOWED_HOSTS = [
    'erfan-clinic.com',
    'www.erfan-clinic.com',
    'localhost',
    '127.0.0.1',
    # اگر از ساب‌دامین استفاده می‌کنی، اینجا هم اضافه کن
]

# =============================================================================
# اپلیکیشن‌ها
# =============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts.apps.AccountsConfig',
    'core',
    'administrator',
    'django_ckeditor_5',
]

# =============================================================================
# میدلورها
# =============================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.CustomErrorMiddleware',
]

ROOT_URLCONF = 'clinic.urls'

# =============================================================================
# تمپلیت‌ها
# =============================================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'clinic.wsgi.application'

# =============================================================================
# دیتابیس (روی cPanel بعداً عوض می‌کنی)
# =============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'clinic',          # اسم دیتابیس روی سرور
        'USER': 'root',            # بعداً یوزر واقعی cPanel رو بذار
        'PASSWORD': '2010',        # بعداً پسورد واقعی رو بذار
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'erfancli_clinic',
#         'USER': 'erfancli_0016588746',
#         'PASSWORD': '@Hadi2010',
#         'HOST': 'localhost',
#         'PORT': '',
#         'OPTIONS': {
#             'charset': 'utf8mb4',
#         },
#     }
# }



# =============================================================================
# اعتبارسنجی پسورد و زبان
# =============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.Profile'

# =============================================================================
# فایل‌های استاتیک و مدیا — مهم‌ترین قسمت برای cPanel
# =============================================================================

# URL استاتیک (همون /static/)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]


# تنظیمات CKEditor 5
CKEDITOR_5_UPLOAD_PATH = "uploads/ckeditor5/"
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': ['heading', '|', 'bold', 'italic', 'link', 
                    'bulletedList', 'numberedList', 'blockQuote', 'imageUpload'],
    },
}

# =============================================================================
# امنیت بیشتر (اختیاری ولی توصیه می‌شود)
# =============================================================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'