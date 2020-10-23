"""
Django settings for YSE_PZ project.

Generated by 'django-admin startproject' using Django 1.11.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
from configparser import RawConfigParser

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
configFile = os.path.join(__location__, 'settings.ini')

config = RawConfigParser()
config.read(configFile)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'f9zh73k2z&-p*k^fzj!sydk03zwlxdm%*13rd9t$*n0i6*sr6%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(config.get('site_settings', 'IS_DEBUG'))

ALLOWED_HOSTS = ['*']


# Application definitionEXPLORER_SQL_BLACKLIST

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'YSE_App.apps.YseAppConfig',
    'rest_framework',
    'rest_framework.authtoken',
    'widget_tweaks',
	'django_tables2',
    'explorer',
	'bootstrap3',
	'django_filters',
	'django_cron',
	'el_pagination',
	#'silk'
]

CRON_CLASSES = [
	'YSE_App.util.TNS_Synopsis.TNS_uploads.TNS_emails',
	'YSE_App.data_ingest.Photo_Z.YSE',
	'YSE_App.data_ingest.SDSS_Photo_Z.YSE',
	'YSE_App.data_ingest.PS1_cutouts.YSE',
	'YSE_App.data_ingest.PS1_PhotoZ.YSE',
	'YSE_App.data_ingest.Apply_Tags.Tags',
	'YSE_App.data_ingest.YSE_observations.SurveyObs',
	'YSE_App.data_ingest.Query_ZTF.AntaresZTF',
	'YSE_App.data_ingest.QUB_data.YSE',
	'YSE_App.data_ingest.Gaia_LC.GaiaLC',
	'YSE_App.data_ingest.QUB_data.YSE_Weekly',
	'YSE_App.data_ingest.QUB_data.QUB',
    'YSE_App.rapid.rapid_classify.rapid_classify_cron',
	'YSE_App.data_ingest.YSE_Forced_Phot.ForcedPhot',
	'YSE_App.data_ingest.YSE_Forced_Phot.ForcedPhotUpdate',
	'YSE_App.data_ingest.TNS_uploads.TNS_updates',
	'YSE_App.data_ingest.TNS_uploads.TNS_Ignore_updates',
	'YSE_App.data_ingest.TNS_uploads.TNS_recent',
    'YSE_App.data_ingest.QUB_data.CheckDuplicates'
]

MIDDLEWARE = [
	#'silk.middleware.SilkyMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]

ROOT_URLCONF = 'YSE_PZ.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(os.path.dirname(__file__), 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
				'django.template.context_processors.request',
				'django.template.context_processors.static'
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', # this is default
)

WSGI_APPLICATION = 'YSE_PZ.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'explorer': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config.get('database', 'DATABASE_NAME'),
        'USER': config.get('database', 'EXPLORER_USER'),
        'PASSWORD': config.get('database', 'EXPLORER_PASSWORD'),
        'HOST': config.get('database', 'DATABASE_HOST'),
        'PORT': config.get('database', 'DATABASE_PORT')
    },
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config.get('database', 'DATABASE_NAME'),
        'USER': config.get('database', 'DATABASE_USER'),
        'PASSWORD': config.get('database', 'DATABASE_PASSWORD'),
        'HOST': config.get('database', 'DATABASE_HOST'),
        'PORT': config.get('database', 'DATABASE_PORT'),
		'OPTIONS': {'ssl': {'ssl_disabled': True}}
    }
}

EXPLORER_CONNECTIONS = { 'Explorer': 'explorer' }
EXPLORER_DEFAULT_CONNECTION = 'explorer'
# Allow all users to access and modify SQL Explorer queries.
EXPLORER_PERMISSION_VIEW = lambda u: u
EXPLORER_PERMISSION_CHANGE = lambda u: u

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
       'rest_framework.authentication.BasicAuthentication',
       'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100
}

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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

LOGIN_URL = config.get('virtual_directory', 'LOGIN_URL')

SMTP_LOGIN = config.get('SMTP_provider', 'SMTP_LOGIN')
SMTP_PASSWORD = config.get('SMTP_provider', 'SMTP_PASSWORD')
SMTP_HOST = config.get('SMTP_provider', 'SMTP_HOST')
SMTP_PORT = config.get('SMTP_provider', 'SMTP_PORT')

KEPLER_API_ENDPOINT = "http://api.keplerscience.org/is-k2-observing"

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'
LOCAL_UTC_OFFSET = -8

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
PROJECT_DIR=os.path.dirname(__file__)
STATIC_ROOT= os.path.join(PROJECT_DIR,'static/')
STATIC_URL = config.get('site_settings', 'STATIC')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
