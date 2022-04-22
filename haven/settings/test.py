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

# Allow local database user login
AUTHENTICATION_BACKENDS.append("django.contrib.auth.backends.ModelBackend")
if "local" not in HAVEN_AUTH_TYPES:
    HAVEN_AUTH_TYPES += ["local"]
    LOCAL_AUTH=True