# Import settings for all components
from haven.settings.authorisation.backends.github import add_backend
from .components.common import *
from .components.easyaudit import *
from .components.email import *
from .components.bleach import *

import environ
import importlib

env = environ.Env()

# Authorisation
from .authorisation.python_social_auth import *
SOCIAL_AUTH_BACKENDS = env.list("SOCIAL_AUTH_BACKENDS", default=["github"])

for backend in SOCIAL_AUTH_BACKENDS:
    importlib.import_module(f"haven.settings.authorisation.backends.{backend}")
    AUTHENTICATION_BACKENDS, AUTH_DISPLAY_NAMES = add_backend(AUTHENTICATION_BACKENDS, AUTH_DISPLAY_NAMES)

