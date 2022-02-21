from configurations import Configuration, values
from pathlib import Path

from haven.settings.auth.remote import AUTHENTICATION_BACKENDS
from haven.settings.components.common import INSTALLED_APPS, MIDDLEWARE

class Base(Configuration):
    # GENERAL
    # ------------------------------------------------------------------------------
    BASE_DIR = Path(__file__).resolve(strict=True).parents[2]
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
    DATABASES = values.DatabaseURLValue('')
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


class RemoteUserMixin(object):
    """Mixin for configuring the application to make use of external
    authentication sources such as Authelia.
    See https://docs.djangoproject.com/en/4.0/howto/auth-remote-user/
    """
    @property
    def MIDDLEWARE(self):
        return [
            "haven.identity.auth.middleware.HttpRemoteUserMiddleware"
        ] + super(RemoteUserMixin, self).MIDDLEWARE

    @property
    def AUTHENTICATION_BACKENDS(self):
        return [
            "haven.identiry.auth.backends.RemoteExtendedUserBackend",
        ] + super(RemoteUserMixin, self).AUTHENTICATION_BACKENDS

    # Logout from authelia after logout from Django app
    @property
    def LOGOUT_REDIRECT_URL(self):
        return "https://auth." + super(RemoteUserMixin, self).BASE_DOMAIN + "/logout"


class LocalUserMixin(object):
    """Enable login with local user accounts"""
    @property
    def AUTHENTICATION_BACKENDS(self):
        return super(LocalUserMixin, self).AUTHENTICATION_BACKENDS + [
            "django.contrib.auth.backends.ModelBackend",
        ]

class SocialAuthMixin(object):
    """Enable login with OAuth2 through a social provider
    like GitHub, ORCID, or Google"""

    SOCIAL_AUTH_LOGIN_ERROR_URL = "/error/"

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

    AUTH_BACKEND_DISPLAY_NAMES = {}


class AzureUserMixin(SocialAuthMixin):
    LOGIN_URL = "/auth/login/azuread-tenant-oauth2/"

    @property
    def AUTHENTICATION_BACKENDS(self):
        return [
            "haven.identity.backends.CustomAzureOAuth2Backend",
        ] + super(AzureUserMixin, self).AUTHENTICATION_BACKENDS

    @property
    def AUTH_BACKEND_DISPLAY_NAMES(self):
        display_names = super(AzureUserMixin, self).AUTH_BACKEND_DISPLAY_NAMES
        display_names["azure-ad-tenant"] = "Azure"
        return display_names

    SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY = values.Value(environ_prefix="")
    SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET = values.Value(environ_prefix="")
    SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID = = values.Value(environ_prefix="")
    SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_RESOURCE = "https://graph.microsoft.com"

    # Haven specific Azure AD settings
    SECURITY_GROUP_SYSTEM_MANAGERS = values.Value(
        "SG SHM Programme Managers",
        environ_prefix=""
    )
    SECURITY_GROUP_PROGRAMME_MANAGERS = values.Value(
        "SG SHM Programme Managers",
        environ_prefix=""
    )
    SECURITY_GROUP_PROJECT_MANAGERS = values.Value(
        "SG SHM Project Managers",
        environ_prefix=""
    )
    AD_RESEARCH_USER_DN = "CN=%(cn)s,OU=Safe Haven Research Users,DC=dsgroupdev,DC=co,DC=uk"
    AD_USER_OBJECT_CLASSES = ["user", "organizationalPerson", "person", "top"]


class GitHubUserMixin(SocialAuthMixin):

    @property
    def AUTHENTICATION_BACKENDS(self):
        return [
            "social_core.backends.github.GithubOAuth2",
        ] + super(GitHubUserMixin, self).AUTHENTICATION_BACKENDS

    @property
    def AUTH_BACKEND_DISPLAY_NAMES(self):
        display_names = super(GitHubUserMixin, self).AUTH_BACKEND_DISPLAY_NAMES
        display_names["github"] = "GitHub"
        return display_names

    SOCIAL_AUTH_GITHUB_KEY = values.Value(environ_prefix="")
    SOCIAL_AUTH_GITHUB_SECRET = values.Value(environ_prefix="")

class Local(Base):
    DEBUG = values.BooleanValue(True)

    # Add debug toolbar
    @property
    def INSTALLED_APPS(self):
        return super(Local, self).INSTALLED_APPS.extend(["debug_toolbar",])

    @property
    def MIDDLEWARE(self):
        return super(Local, self).MIDDLEWARE.insert(
            0, "debug_toolbar.middleware.DebugToolbarMiddleware"
            )

    # Log all emails to console
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

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


class Development(Base):
    # Settings for using Django with a proxy
    SECURE_SSL_REDIRECT = False
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True

    # Allows browsers to ensure cookies are secure
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Enforce SSL for database communication
    @property
    def DATABASES(self):
        dbs = super(Development, self).DATABASES
        dbs["default"].setdefault("OPTIONS", {})
        dbs["default"]["OPTIONS"]["sslmode"] = "require"
        return dbs

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
    """Currently identical to Development"""
    pass


class Test(Base):
    SAFE_HAVEN_DOMAIN = "example.com"
    # This should prevent Whitenoise from looking in a non-existent directory and raising a warning
    # during every test
    WHITENOISE_AUTOREFRESH = True


class LocalUserLocal(LocalUserMixin, Local):
    pass

class LocalUserProduction(LocalUserMixin, Production):
    pass

class RemoteUserLocal(LocalUserMixin, RemoteUserMixin, Local):
    pass

class RemoteUserProduction(RemoteUserMixin, Production):
    pass

class GitHubUserLocal(LocalUserMixin, GitHubUserMixin, Local):
    pass

class GitHubUserProduction(GitHubUserMixin, Production):
    pass

class AzureUserProduction(AzureUserMixin, Production):
    pass

