from pathlib import Path

from configurations import Configuration, values
from .custom_values import DataBaseURLValueExtra


BASE_DIR = Path(__file__).resolve().parents[2]

class Base(Configuration):
    DOTENV = BASE_DIR / ".env"

    # GENERAL
    # ------------------------------------------------------------------------------
    
    # https://docs.djangoproject.com/en/dev/ref/settings/#debug
    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = values.BooleanValue(False)
    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = values.SecretValue()

    ALLOWED_HOSTS = values.ListValue([])

    WEBAPP_TITLE = values.Value("Data Classification")

    INTERNAL_IPS = values.ListValue(["127.0.0.1"])
    SAFE_HAVEN_DOMAIN = values.Value("dsgroupdev.co.uk")
    BASE_DOMAIN = values.Value("localhost:8000")
    BASE_URL = values.Value("http://localhost:8000/")

    # DATABASES
    # ------------------------------------------------------------------------------
    # https://docs.djangoproject.com/en/dev/ref/settings/#databases
    DATABASES = DataBaseURLValueExtra()

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

    DEV_APPS = [
        "debug_toolbar"
    ]

    # https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
    @property
    def INSTALLED_APPS(self):
        apps = self.THIRD_PARTY_PRE_APPS + self.DJANGO_APPS \
               + self.THIRD_PARTY_APPS + self.LOCAL_APPS
        if self.DEBUG:
            apps += self.DEV_APPS
        return apps

    # MIDDLEWARE
    # ------------------------------------------------------------------------------
    # https://docs.djangoproject.com/en/dev/ref/settings/#middleware
    @property
    def MIDDLEWARE(self):
        middleware = [
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
        if self.DEBUG:
            middleware += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
        return middleware

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
    AUTHENTICATION_BACKENDS = []
    # https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
    AUTH_USER_MODEL = "identity.User"
    # https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
    LOGIN_REDIRECT_URL = "/projects"
    LOGOUT_REDIRECT_URL = "home"
    # https://docs.djangoproject.com/en/dev/ref/settings/#login-url
    LOGIN_URL = "login"

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

    # PHONENUMBER
    # ------------------------------------------------------------------------------
    PHONENUMBER_DEFAULT_REGION = "GB"

    # Bleach
    # ------------------------------------------------------------------------------
    BLEACH_ALLOWED_TAGS = ["a", "em", "li", "ol", "p", "strong", "ul"]

    # EasyAudit
    # ------------------------------------------------------------------------------
    DJANGO_EASY_AUDIT_WATCH_AUTH_EVENTS = False
    DJANGO_EASY_AUDIT_WATCH_REQUEST_EVENTS = False

    # EMAIL
    # ------------------------------------------------------------------------------
    EMAIL = values.EmailURLValue("")


class Local(Base):
    DEBUG = values.BooleanValue(True)
    
    # Log all emails to console
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

    # Enable login with local user accounts
    @property
    def AUTHENTICATION_BACKENDS(self):
        return super(Local, self).AUTHENTICATION_BACKENDS + [
            "django.contrib.auth.backends.ModelBackend",
        ]

    # Don't make life difficult for ourselves with password restrictions on dev
    AUTH_PASSWORD_VALIDATORS = []

    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "root": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
        "formatters": {
            "verbose": {
                "format": "%(levelname)s %(asctime)s %(module)s "
                "%(process)d %(thread)d %(message)s"
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            }
        },
    }

class Test(Base):
    SAFE_HAVEN_DOMAIN = "example.com"
    # This should prevent Whitenoise from looking in a non-existent directory and raising a warning
    # during every test
    WHITENOISE_AUTOREFRESH = True

class Development(Base):
    # Settings for using Django with a proxy
    SECURE_SSL_REDIRECT = False
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True

    # Allows browsers to ensure cookies are secure
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Enforce SSL for database communication and tie transactions
    # to http requests
    DATABASES = DataBaseURLValueExtra(ssl_require=True, atomic=True)

    # Log to the console so it will be captured by Azure's log stream
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "%(levelname)s %(asctime)s %(module)s "
                "%(process)d %(thread)d %(message)s"
            },
        },
        "handlers": {
            "console": {
                "level": "WARNING",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": "WARNING",
            },
        },
    }

class Production(Development):
    """Currently the same as Development"""
    pass