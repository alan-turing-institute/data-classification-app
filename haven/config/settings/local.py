# flake8: noqa F405
from haven.config.settings.base import *  # noqa


# Settings specific to the local machine development environment

DEBUG = True
ALLOWED_HOSTS = ['*']

# Enable debug toolbar
INSTALLED_APPS.extend([
    'debug_toolbar',
])

# Add debug toolbar
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# Allow local database user login
AUTHENTICATION_BACKENDS.append('django.contrib.auth.backends.ModelBackend')

# Log all emails to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Don't make life difficult for ourselves with password restrictions on dev
AUTH_PASSWORD_VALIDATORS = []

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'DEBUG',
        'handlers': ['console'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
}
