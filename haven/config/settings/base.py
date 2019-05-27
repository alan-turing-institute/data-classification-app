"""
Django settings for haven project.

Generated by 'django-admin startproject' using Django 2.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
from pathlib import Path

import environ


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(os.path.abspath(__file__)).parents[2]


env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)
environ.Env.read_env(str(BASE_DIR / '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])


# Application definition

THIRD_PARTY_PRE_APPS = [
    'dal',
    'dal_select2',
]

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'crispy_forms',
    'debug_toolbar',
    'social_django',
]

LOCAL_APPS = [
    'identity',
    'projects',
    'data',
]

INSTALLED_APPS = THIRD_PARTY_PRE_APPS + DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(BASE_DIR / 'templates')],
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

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASES = {
    'default': env.db_url('DATABASE_URL', default='postgres:///haven'),
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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

AUTHENTICATION_BACKENDS = [
    'identity.backends.CustomAzureOAuth2Backend',
]

AUTH_USER_MODEL = 'identity.User'

SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY = env.str('AZUREAD_OAUTH2_KEY')
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET = env.str('AZUREAD_OAUTH2_SECRET')
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID = env.str('AZUREAD_OAUTH2_TENANT_ID')
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_RESOURCE = 'https://graph.microsoft.com'

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'identity.pipeline.find_existing_user',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'identity.pipeline.user_fields',
    'identity.pipeline.determine_role',
)

LOGIN_REDIRECT_URL = '/projects'
LOGOUT_REDIRECT_URL = 'home'
LOGIN_URL = '/auth/login/azuread-tenant-oauth2/'


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = str(BASE_DIR / 'staticfiles')
STATICFILES_DIRS = [
    str(BASE_DIR / 'static'),
]

INTERNAL_IPS = env.list('INTERNAL_IPS', default=['127.0.0.1'])  # noqa

CRISPY_TEMPLATE_PACK = 'bootstrap4'

SAFE_HAVEN_DOMAIN = env.str('SAFE_HAVEN_DOMAIN', default='dsgroupdev.co.uk')


USE_LDAP = env.bool('USE_LDAP', default=True)
LDAP_SERVER = env.str('LDAP_SERVER', default='')
LDAP_USER = env.str('LDAP_USER', default='')
LDAP_PASSWORD = env.str('LDAP_PASSWORD', default='')


BASE_URL = env.str('BASE_URL', default='http://localhost:8000/')

SYS_CONTROLLER_GROUP_NAME = 'SG System Controllers'

AD_RESEARCH_USER_DN = 'CN=%(cn)s,OU=Safe Haven Research Users,DC=dsgroupdev,DC=co,DC=uk'

AD_USER_OBJECT_CLASSES = ['user', 'organizationalPerson', 'person', 'top']

EMAIL_HOST = env.str('EMAIL_HOST', default='')
if EMAIL_HOST:
    EMAIL_HOST_USER = env.str('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD')
    EMAIL_PORT = env.int('EMAIL_PORT', default=587)
    EMAIL_USE_TLS = env.int('EMAIL_USE_TLS', default=True)

DEFAULT_FROM_MAIL = env.str('FROM_MAIL', default='noreply@dsgroupdev.co.uk')

SOCIAL_AUTH_LOGIN_ERROR_URL = '/error/'
