import environ

env = environ.Env()

AUTHENTICATION_BACKEND = "haven.identity.backends.CustomAzureOAuth2Backend"
AUTH_DISPLAY_NAME = "Azure"
LOGIN_URL = "/auth/login/azuread-tenant-oauth2/"

SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY = env.str("AZUREAD_OAUTH2_KEY", default="")
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET = env.str("AZUREAD_OAUTH2_SECRET", default="")
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID = env.str(
    "AZUREAD_OAUTH2_TENANT_ID", default=""
)
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_RESOURCE = "https://graph.microsoft.com"

SECURITY_GROUP_SYSTEM_MANAGERS = env.str(
    "SECURITY_GROUP_SYSTEM_MANAGERS", default="SG SHM System Managers"
)
SECURITY_GROUP_PROGRAMME_MANAGERS = env.str(
    "SECURITY_GROUP_PROGRAMME_MANAGERS", default="SG SHM Programme Managers"
)
SECURITY_GROUP_PROJECT_MANAGERS = env.str(
    "SECURITY_GROUP_PROGRAMME_MANAGERS", default="SG SHM Project Managers"
)
AD_RESEARCH_USER_DN = "CN=%(cn)s,OU=Safe Haven Research Users,DC=dsgroupdev,DC=co,DC=uk"

AD_USER_OBJECT_CLASSES = ["user", "organizationalPerson", "person", "top"]

# Choose which Django system checks to silence
SILENCED_SYSTEM_CHECKS = [
    "security.W004",
    "security.W008",
    "security.W009",
    "security.W020",
]
# security.W004: Disable HSTS with Azure domain; should enable for custom domain
# security.W008: SSL termination and redirection by Azure
# security.W009: SECRET_KEY is set in deployment
# security.W020: ALLOWED_HOSTS is set in deployment