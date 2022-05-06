import os


os.environ["SECRET_KEY"] = "notasecret"
os.environ["DATABASE_URL"] = "sqlite:////tmp/my-tmp-sqlite.db"


from haven.settings.base import *  # noqa


SAFE_HAVEN_DOMAIN = "example.com"
# This should prevent Whitenoise from looking in a non-existent directory and raising a warning
# during every test
WHITENOISE_AUTOREFRESH = True
