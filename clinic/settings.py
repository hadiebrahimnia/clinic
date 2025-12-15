import pymysql
pymysql.install_as_MySQLdb()
from pathlib import Path
import os
import environ

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, 'django-insecure-default-change-me'),
)

# خواندن فایل .env در محیط لوکال (اگر وجود داشته باشه)
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(BASE_DIR / '.env')


# =============================================================================
# تنظیمات امنیتی و هاست (برای پروداکشن)
# =============================================================================
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

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
        'NAME': env('DATABASE_NAME'),          # اسم دیتابیس روی سرور
        'USER': env('DATABASE_USER'),            # بعداً یوزر واقعی cPanel رو بذار
        'PASSWORD': env('DATABASE_PASSWORD'),        # بعداً پسورد واقعی رو بذار
        'HOST': env('DATABASE_HOST'),
        'PORT': env('DATABASE_PORT'),
    }
}

DATABASES['default']['OPTIONS'] = {'charset': 'utf8mb4'}

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

# جایی که collectstatic همه فایل‌ها رو جمع می‌کنه → این خط باعث رفع ارور می‌شه
STATIC_ROOT = BASE_DIR / 'staticfiles'        # پوشه‌ای که روی سرور سرو می‌شه

# اگر خودت هم پوشه static داخل پروژه داری (css/js/img و …)
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# مدیا (فایل‌های آپلود شده توسط کاربر و CKEditor)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'               # پوشه media در ریشه پروژه

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