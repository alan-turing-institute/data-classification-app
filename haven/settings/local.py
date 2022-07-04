# flake8: noqa F405
import os
import socket

from haven.settings.base import *  # noqa


# Settings specific to the local machine development environment

DEBUG = True
ALLOWED_HOSTS = ["*"]

### Add debug toolbar
INSTALLED_APPS.extend(
    [
        "debug_toolbar",
        "django_extensions",
    ]
)

MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

# required for debug toolbar if using docker
if DEBUG:
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[:-1] + "1" for ip in ips] + ["127.0.0.1", "10.0.2.2"]


# Allow local database user login
AUTHENTICATION_BACKENDS.append("django.contrib.auth.backends.ModelBackend")
if "local" not in HAVEN_AUTH_TYPES:
    HAVEN_AUTH_TYPES += ["local"]

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
            "format": "%(levelname)s %(asctime)s %(module)s " "%(process)d %(thread)d %(message)s"
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
