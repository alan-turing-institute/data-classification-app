from .base import *  # noqa

# DEBUG must be False for production deployments
DEBUG = False

# Settings for using Django with a proxy
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# Allows browsers to ensure cookies are secure
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Enforce SSL for database communication
DATABASES['default'].setdefault('OPTIONS', {})
DATABASES['default']['OPTIONS']['sslmode'] = 'require'

# Name of the Azure security group for System Managers
SYS_CONTROLLER_GROUP_NAME = 'SG System Controllers'
PROG_MANAGER_GROUP_NAME = 'SG SHM Programme Managers'

# Log to the console so it will be captured by Azure's log stream
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    }
}
