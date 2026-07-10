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
    'django_ckeditor_5',
    'ckeditor',
    'ckeditor_uploader',    
    'accounts.apps.AccountsConfig',
    'appointment',
    'core',
    'management',
    'assessments',
    
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
        'NAME': env('DATABASE_NAME'),        
        'USER': env('DATABASE_USER'),          
        'PASSWORD': env('DATABASE_PASSWORD'),      
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
# STATIC_ROOT = BASE_DIR / 'staticfiles'        # پوشه‌ای که روی سرور سرو می‌شه
# STATIC_ROOT = '/home/erfancli/public_html/static'
STATIC_ROOT = env('STATIC_ROOT')
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



CKEDITOR_UPLOAD_PATH = 'media/ckeditor/'
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 400,
        'width': '100%',

        'extraAllowedContent': True,
        'allowedContent': True,

        'language': 'fa',  # بهتر است fa باشد اگر محتوای فارسی است

        # === فونت و اندازه پیش‌فرض ===
        'font_names': 'Vazirmatn;vazirmatn',
        'font_defaultLabel': 'Vazirmatn',
        'fontSize_sizes': '14/14px',
        'fontSize_defaultLabel': '14',

        # اعمال فونت و اندازه به محتوای ویرایشگر
        'contentsCss': [
            """
            body {
                font-family: 'vazirmatn', sans-serif !important;
                font-size: 14px !important;
                line-height: 1.6 !important;
            }
            """
        ],

        'toolbar_Full': [
            ['Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Undo', 'Redo'],
            ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript', '-', 'RemoveFormat'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent'],
            ['Blockquote', 'CreateDiv'],
            ['JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink', 'Anchor'],
            ['Image', 'Table', 'HorizontalRule', 'SpecialChar'],
            ['Styles', 'Format', 'Font', 'FontSize'],
            ['TextColor', 'BGColor'],
            ['Maximize', 'ShowBlocks', 'Source']
        ],

        'extraPlugins': ','.join([
            'uploadimage', 'image2', 'codesnippet', 'widget', 'lineutils', 'clipboard',
        ]),

        'filebrowserUploadUrl': '/ckeditor/upload/',
        'filebrowserBrowseUrl': '/ckeditor/browse/',
    },

    'PsychologistDocument': {
        'toolbar': [
            ['Bold', 'Italic', 'Underline'],
            ['BulletedList', 'NumberedList'],
        ],
        'height': 200,
        'width': '100%',


        'font_names': 'vazirmatn',
        'font_defaultLabel': 'vazirmatn',
        'fontSize_sizes': '14/14px',
        'fontSize_defaultLabel': '14',

        'contentsCss': [
            """
            body {
                font-family: 'vazirmatn'!important;
                font-size: 14px !important;
                line-height: 1.7 !important;
            }
            """
        ],
    },
}