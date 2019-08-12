import os


os.environ['SECRET_KEY'] = 'notasecret'
os.environ['AZUREAD_OAUTH2_KEY'] = 'notasecret'
os.environ['AZUREAD_OAUTH2_SECRET'] = 'notasecret'
os.environ['AZUREAD_OAUTH2_TENANT_ID'] = 'notasecret'
os.environ['DATABASE_URL'] = 'sqlite:////tmp/my-tmp-sqlite.db'


from .base import *  # noqa


USE_LDAP = False
SAFE_HAVEN_DOMAIN = 'example.com'