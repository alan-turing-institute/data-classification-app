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
environ.Env.read_env(str(BASE_DIR / ".env"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY", default="")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", default=False)

WEBAPP_TITLE = env.str("WEBAPP_TITLE", default="Data Classification")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])


# Application definition

THIRD_PARTY_PRE_APPS = [
    "dal",
    "dal_select2",
    "whitenoise.runserver_nostatic",  # Let WhiteNoise handle static files in local development instead of Django, for consistency with production
]

DJANGO_APPS = [
    "django.contrib.admin",  # admin currently required by django-easy-audit
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.forms",
]

THIRD_PARTY_APPS = [
    "crispy_forms",
    "django_bleach",
    "django_tables2",
    "easyaudit",
    "simple_history",
    "social_django",
    "taggit",
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "two_factor"
]

LOCAL_APPS = [
    "haven.core",
    "haven.identity",
    "haven.projects",
    "haven.data",
]

INSTALLED_APPS = THIRD_PARTY_PRE_APPS + DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


MIDDLEWARE = [
    "django.middleware.common.BrokenLinkEmailsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
    "easyaudit.middleware.easyaudit.EasyAuditMiddleware",
]

ROOT_URLCONF = "haven.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(BASE_DIR / "haven" / "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "sourcerevision.context_processors.source_revision",
            ],
            "libraries": {"haven": "haven.core.templatetags.haven",},
        },
    },
]

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

WSGI_APPLICATION = "haven.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASES = {
    "default": env.db_url("DATABASE_URL", default="postgres:///haven"),
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]

AUTHENTICATION_BACKENDS = [
    "haven.identity.backends.CustomAzureOAuth2Backend",
]

AUTH_USER_MODEL = "identity.User"

SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY = env.str("AZUREAD_OAUTH2_KEY", default="")
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET = env.str("AZUREAD_OAUTH2_SECRET", default="")
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID = env.str(
    "AZUREAD_OAUTH2_TENANT_ID", default=""
)
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_RESOURCE = "https://graph.microsoft.com"

SECURITY_GROUP_SYSTEM_MANAGERS = env.str(
    "SECURITY_GROUP_SYSTEM_MANAGERS", default="SG SHM System Managers"
)
SECURITY_GROUP_PROGRAMME_MANAGERS = env.str(
    "SECURITY_GROUP_PROGRAMME_MANAGERS", default="SG SHM Programme Managers"
)
SECURITY_GROUP_PROJECT_MANAGERS = env.str(
    "SECURITY_GROUP_PROGRAMME_MANAGERS", default="SG SHM Project Managers"
)

SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "haven.identity.pipeline.find_existing_user",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
    "haven.identity.pipeline.user_fields",
    "haven.identity.pipeline.determine_role",
)

LOGIN_REDIRECT_URL = "/projects"
LOGOUT_REDIRECT_URL = "home"
#LOGIN_URL = "/auth/login/azuread-tenant-oauth2/"
LOGIN_URL = "two_factor:login"
#LOGIN_REDIRECT_URL = "two_factor:profile"


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-gb"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [
    str(BASE_DIR / "static"),
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

INTERNAL_IPS = env.list("INTERNAL_IPS", default=["127.0.0.1"])  # noqa

CRISPY_TEMPLATE_PACK = "bootstrap4"
DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap4.html"

SAFE_HAVEN_DOMAIN = env.str("SAFE_HAVEN_DOMAIN", default="dsgroupdev.co.uk")

BASE_URL = env.str("BASE_URL", default="http://localhost:8000/")

AD_RESEARCH_USER_DN = "CN=%(cn)s,OU=Safe Haven Research Users,DC=dsgroupdev,DC=co,DC=uk"

AD_USER_OBJECT_CLASSES = ["user", "organizationalPerson", "person", "top"]

EMAIL_HOST = env.str("EMAIL_HOST", default="")
if EMAIL_HOST:
    EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default="")
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_USE_TLS = env.int("EMAIL_USE_TLS", default=True)

DEFAULT_FROM_MAIL = env.str("FROM_MAIL", default="noreply@dsgroupdev.co.uk")

SOCIAL_AUTH_LOGIN_ERROR_URL = "/error/"

PHONENUMBER_DEFAULT_REGION = "GB"

BLEACH_ALLOWED_TAGS = ["a", "em", "li", "ol", "p", "strong", "ul"]

DJANGO_EASY_AUDIT_WATCH_AUTH_EVENTS = False
DJANGO_EASY_AUDIT_WATCH_REQUEST_EVENTS = False

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Choose which Django system checks to silence
SILENCED_SYSTEM_CHECKS = [
    "security.W004",
    "security.W008",
    "security.W009",
    "security.W020",
]
# security.W004: Disable HSTS with Azure domain; should enable for custom domain
# security.W008: SSL termination and redirection by Azure
# security.W009: SECRET_KEY is set in deployment
# security.W020: ALLOWED_HOSTS is set in deployment
