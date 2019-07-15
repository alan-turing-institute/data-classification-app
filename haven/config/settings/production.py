from .base import *  # noqa


SECURE_SSL_REDIRECT = True

DEBUG = False

DATABASES['default']['OPTIONS'] = {'sslmode':'require'}

