import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from haven.settings.base import *  # noqa


# DEBUG must be False for production deployments
DEBUG = False

# Settings for using Django with a proxy
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# Allows browsers to ensure cookies are secure
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Enforce SSL for database communication (if needed)
# DATABASES["default"].setdefault("OPTIONS", {})
# DATABASES["default"]["OPTIONS"]["sslmode"] = "require"

# Log to the console so it will be captured by Azure's log stream
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s " "%(process)d %(thread)d %(message)s"
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

ENABLE_SENTRY = env.bool("ENABLE_SENTRY", default=False)  # noqa

if ENABLE_SENTRY:
    # Initialise Sentry
    SENTRY_DSN = env.str("SENTRY_DSN")  # noqa
    sentry_sdk.init(dsn=SENTRY_DSN, integrations=[DjangoIntegration()])
