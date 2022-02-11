import environ

env = environ.Env()

AUTHENTICATION_BACKEND = "social_core.backends.orcid.ORCIDOAuth2Sandbox"
AUTH_DISPLAY_NAME = "ORCID Sandbox"

SOCIAL_AUTH_ORCID_SANDBOX_KEY = env.str("ORCID_OAUTH2_KEY", default="")
SOCIAL_AUTH_ORCID_SANDBOX_SECRET = env.str("ORCID_OAUTH2_SECRET", default="")