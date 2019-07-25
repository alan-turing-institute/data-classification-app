from .base import *  # noqa


SECURE_SSL_REDIRECT = False
# SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

DEBUG = False

DATABASES['default']['OPTIONS'] = {'sslmode':'require'}

