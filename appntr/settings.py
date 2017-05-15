"""
Django settings for appntr project.

Generated by 'django-admin startproject' using Django 1.10.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os
import dj_database_url


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ON_DOKKU = os.environ.get('DOKKU_APP_TYPE', False)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', '$g4n7bmd#7aw(t-uu=))h#k@u9u$u_u*&2grwzyg9=&t32o4%-')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = not ON_DOKKU

ALLOWED_HOSTS = os.environ.get('DOMAINS', 'localhost').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'appntr'
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

ROOT_URLCONF = 'appntr.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'appntr.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(default='sqlite://./db.sqlite3')
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

if ON_DOKKU:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    # EMAIL_USE_TLS = True
    EMAIL_USE_SSL = True
    DEFAULT_FROM_EMAIL = 'robot@demokratie-in-bewegung.org'
    EMAIL_HOST = os.environ.get("SMTP_SERVER", "smtp.mailgun.org")
    EMAIL_HOST_USER = os.environ.get("SMTP_USERNAME", 'mymail@gmail.com')
    EMAIL_HOST_PASSWORD = os.environ.get("SMTP_PASSWORD", 'password')
    EMAIL_PORT = int(os.environ.get("SMTP_PORT", 587))
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'de'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'



#### LOOMIO

LOOMIO_INCOMING_GROUP = int(os.environ.get("LOOMIO_INCOMING_GROUP", "3"))
LOOMIO_REJECTED_GROUP = int(os.environ.get("LOOMIO_REJECTED_GROUP", "4"))
LOOMIO_ACCEPTED_GROUP = int(os.environ.get("LOOMIO_ACCEPTED_GROUP", "2"))
LOOMIO_BACKBURNER_GROUP = int(os.environ.get("LOOMIO_BACKBURNER_GROUP", "5"))
LOOMIO_CLIENT_ID = os.environ.get("LOOMIO_CLIENT_ID")
LOOMIO_CLIENT_SECRET = os.environ.get("LOOMIO_CLIENT_SECRET")

LOOMIO_POSTPONE_BY_HOURS = 6


# app specific
MIN_VOTERS = 5