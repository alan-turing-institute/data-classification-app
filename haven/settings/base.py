from pathlib import Path

import environ


BASE_DIR = Path(__file__).resolve(strict=True).parents[2]

env = environ.Env()

ENVIRONMENT = env.str("DJANGO_ENVIRONMENT", default="local")

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

WEBAPP_TITLE = env.str("WEBAPP_TITLE", default="Data Classification")

INTERNAL_IPS = env.list("INTERNAL_IPS", default=["127.0.0.1"])  # noqa
SAFE_HAVEN_DOMAIN = env.str("SAFE_HAVEN_DOMAIN", default="example.com")
BASE_DOMAIN = env.str("BASE_DOMAIN", default="localhost:8000")
BASE_URL = env.str("BASE_URL", default="http://localhost:8000/")

DEFAULT_QUESTION_SET_NAME = env.str("DEFAULT_QUESTION_SET_NAME", default="turing")

# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {"default": env.db()}
DATABASES["default"]["ATOMIC_REQUESTS"] = True

# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = "UTC"
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en-gb"
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True
# https://docs.djangoproject.com/en/dev/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = "haven.urls"
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "haven.wsgi.application"

# APPS
# ------------------------------------------------------------------------------
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
]

LOCAL_APPS = [
    "haven.core",
    "haven.identity",
    "haven.projects",
    "haven.data",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = THIRD_PARTY_PRE_APPS + DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
MIDDLEWARE = [
    "django.middleware.common.BrokenLinkEmailsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
    "easyaudit.middleware.easyaudit.EasyAuditMiddleware",
]

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
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
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
                "haven.core.context_processors.auth_types",
            ],
            "libraries": {
                "haven": "haven.core.templatetags.haven",
            },
        },
    },
]

# https://docs.djangoproject.com/en/dev/ref/settings/#form-renderer
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap4"

# https://django-tables2.readthedocs.io/en/latest/pages/custom-rendering.html
DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap4.html"

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = True
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"

# AUTHENTICATION
# ------------------------------------------------------------------------------

# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = "identity.User"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = "/projects"
LOGOUT_REDIRECT_URL = "home"
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = "login"

HAVEN_AUTH_TYPES = env.list("AUTH_TYPES", default=["local"])

AUTHENTICATION_BACKENDS = []
if "remote" in HAVEN_AUTH_TYPES:
    AUTHENTICATION_BACKENDS += [
        "haven.identity.auth.backends.RemoteExtendedUserBackend",
    ]
    MIDDLEWARE.append("haven.identity.auth.middleware.HttpRemoteUserMiddleware")
    LOGOUT_REDIRECT_URL = "https://auth." + BASE_DOMAIN + "/logout"
if "social" in HAVEN_AUTH_TYPES:
    from .components.social_auth import *

    SOCIAL_AUTH_PROVIDERS = env.list("SOCIAL_AUTH_PROVIDERS", default=[])
    SOCIAL_AUTH_BACKEND_DISPLAY_NAMES = {}
    for provider in SOCIAL_AUTH_PROVIDERS:
        AUTHENTICATION_BACKENDS += [provider_dictionary[provider]["backend"]]
        SOCIAL_AUTH_BACKEND_DISPLAY_NAMES[provider] = provider_dictionary[provider]["display_name"]
if "local" in HAVEN_AUTH_TYPES:
    AUTHENTICATION_BACKENDS += [
        "django.contrib.auth.backends.ModelBackend",
    ]
    LOCAL_AUTH = True


# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# STATIC
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(BASE_DIR / "staticfiles")
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [
    str(BASE_DIR / "static"),
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# EMAIL
# ------------------------------------------------------------------------------
EMAIL_HOST = env.str("EMAIL_HOST", default="")
if EMAIL_HOST:
    EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default="")
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)

DEFAULT_FROM_MAIL = env.str("FROM_MAIL", default="noreply@dsgroupdev.co.uk")

# THIRD PARTY SETTINGS
# ------------------------------------------------------------------------------
PHONENUMBER_DEFAULT_REGION = "GB"
BLEACH_ALLOWED_TAGS = ["a", "em", "li", "ol", "p", "strong", "ul"]
DJANGO_EASY_AUDIT_WATCH_AUTH_EVENTS = False
DJANGO_EASY_AUDIT_WATCH_REQUEST_EVENTS = False
