import os


os.environ["SECRET_KEY"] = "notasecret"
os.environ["AZUREAD_OAUTH2_KEY"] = "notasecret"
os.environ["AZUREAD_OAUTH2_SECRET"] = "notasecret"
os.environ["AZUREAD_OAUTH2_TENANT_ID"] = "notasecret"
os.environ["DATABASE_URL"] = "sqlite:////tmp/my-tmp-sqlite.db"


from haven.settings.base import *  # noqa


SAFE_HAVEN_DOMAIN = "example.com"
# This should prevent Whitenoise from looking in a non-existent directory and raising a warning
# during every test
WHITENOISE_AUTOREFRESH = True

# Azure AD Tenant settings
# Names of the Azure AD security groups used to give system-level permissions to users
SECURITY_GROUP_SYSTEM_MANAGERS = "SG SHM System Managers"
SECURITY_GROUP_PROGRAMME_MANAGERS = "SG SHM Programme Managers"
SECURITY_GROUP_PROJECT_MANAGERS = "SG SHM Project Managers"
