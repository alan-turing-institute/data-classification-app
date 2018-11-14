from .base import *  # noqa


# Settings specific to the development environment

DEBUG = True
ALLOWED_HOSTS = ['*']

# Log all emails to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Don't make life difficult for ourselves with password restrictions on dev
AUTH_PASSWORD_VALIDATORS = []

INTERNAL_IPS = env.list('INTERNAL_IPS', default=['127.0.0.1'])  # noqa
