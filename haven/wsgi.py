"""
WSGI config for haven project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "haven.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", "LocalUserProduction")

from configurations.wsgi import get_wsgi_application

application = get_wsgi_application()
