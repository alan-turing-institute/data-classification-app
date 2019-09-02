import os


os.environ['SECRET_KEY'] = 'notasecret'
os.environ['AZUREAD_OAUTH2_KEY'] = 'notasecret'
os.environ['AZUREAD_OAUTH2_SECRET'] = 'notasecret'
os.environ['AZUREAD_OAUTH2_TENANT_ID'] = 'notasecret'
os.environ['DATABASE_URL'] = 'sqlite:////tmp/my-tmp-sqlite.db'


from .base import *  # noqa


# Name of the Azure security group for System Managers
SYS_CONTROLLER_GROUP_NAME = 'SG SHM System Managers'

USE_LDAP = False
SAFE_HAVEN_DOMAIN = 'example.com'
# This should prevent Whitenoise from looking in a non-existent directory and raising a warning 
# during every test
WHITENOISE_AUTOREFRESH = True