from pathlib import Path
import os
import sys

BASE_DIR = Path(__file__).resolve().parent.parent  # .../project_jivapms

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-key-change-me')
DEBUG = True
ALLOWED_HOSTS = ['*']

# Site metadata (overridable via environment)
SITE_NAME = os.environ.get('SITE_NAME', 'JIVAPMS')
SITE_HEADER = os.environ.get('SITE_HEADER', 'JIVAPMS Admin')
SITE_TAGLINE = os.environ.get('SITE_TAGLINE', 'Product and Project Management System')
BUILD_VERSION = os.environ.get('BUILD_VERSION', '0.1.0')
BUILD_DATE = os.environ.get('BUILD_DATE', '')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # local apps
    'apps.app_0.apps.App0Config',
    'apps.app_admin.apps.AppAdminConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR.parent / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.app_0.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static outside project directory
PROJECT_ROOT = BASE_DIR.parent  # .../jivapms_oct25
STATIC_URL = '/static/'
STATIC_ROOT = PROJECT_ROOT / 'staticfiles'
STATICFILES_DIRS = [PROJECT_ROOT / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Make 'apps' importable via top-level
APPS_PARENT = PROJECT_ROOT  # contains 'apps/'
if str(APPS_PARENT) not in sys.path:
    sys.path.insert(0, str(APPS_PARENT))

# Auth
LOGIN_URL = '/admin/login/'