from .base import *  # noqa


SECURE_SSL_REDIRECT = False
# SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True


DATABASES['default']['OPTIONS'] = {'sslmode':'require'}

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
        'logfile': {
            'level': 'WARNING',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': 'D:\home\site\wwwroot\haven.log',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['logfile'],
            'level': 'WARNING',
            'propagate': False,
        }
    }
}
