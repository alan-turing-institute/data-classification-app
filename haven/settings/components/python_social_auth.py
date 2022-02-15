import environ

env = environ.Env()

SOCIAL_AUTH_LOGIN_ERROR_URL = "/error/"

SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "haven.identity.pipeline.find_existing_user",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
    "haven.identity.pipeline.user_fields",
    "haven.identity.pipeline.determine_role",
)

# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = []
AUTH_BACKEND_DISPLAY_NAMES = {}  # Used by custom template filter

# PROVIDERS
# ------------------------------------------------------------------------------
# Uncomment provider sections as required

## GitHub
AUTHENTICATION_BACKENDS.extend(["social_core.backends.github.GithubOAuth2"])
AUTH_BACKEND_DISPLAY_NAMES["github"] = "GitHub"

SOCIAL_AUTH_GITHUB_KEY = env.str("SOCIAL_AUTH_GITHUB_KEY", default="")
SOCIAL_AUTH_GITHUB_SECRET = env.str("SOCIAL_AUTH_GITHUB_SECRET", default="")

## ORCID Sandbox
AUTHENTICATION_BACKENDS.extend(["social_core.backends.orcid.ORCIDOAuth2Sandbox"])
AUTH_BACKEND_DISPLAY_NAMES["orcid-sandbox"] = "ORCID Sandbox"

SOCIAL_AUTH_ORCID_SANDBOX_KEY = env.str("SOCIAL_AUTH_ORCID_SANDBOX_KEY", default="")
SOCIAL_AUTH_ORCID_SANDBOX_SECRET = env.str("SOCIAL_AUTH_ORCID_SANDBOX_SECRET", default="")

## Azure AD Tenant
# AUTHENTICATION_BACKENDS.extend(["haven.identity.backends.CustomAzureOAuth2Backend"])
# AUTH_BACKEND_DISPLAY_NAMES["azure-ad-tenant"] = "Azure"

# SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY = env.str("AZUREAD_OAUTH2_KEY", default="")
# SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET = env.str("AZUREAD_OAUTH2_SECRET", default="")
# SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID = env.str(
#     "AZUREAD_OAUTH2_TENANT_ID", default=""
# )
# SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_RESOURCE = "https://graph.microsoft.com"

# # If Azure is the exclusive auth provider
# # LOGIN_URL = "/auth/login/azuread-tenant-oauth2/"

# # Haven specific Azure AD settings
# SECURITY_GROUP_SYSTEM_MANAGERS = env.str(
#     "SECURITY_GROUP_SYSTEM_MANAGERS", default="SG SHM System Managers"
# )
# SECURITY_GROUP_PROGRAMME_MANAGERS = env.str(
#     "SECURITY_GROUP_PROGRAMME_MANAGERS", default="SG SHM Programme Managers"
# )
# SECURITY_GROUP_PROJECT_MANAGERS = env.str(
#     "SECURITY_GROUP_PROGRAMME_MANAGERS", default="SG SHM Project Managers"
# )
# AD_RESEARCH_USER_DN = "CN=%(cn)s,OU=Safe Haven Research Users,DC=dsgroupdev,DC=co,DC=uk"

# AD_USER_OBJECT_CLASSES = ["user", "organizationalPerson", "person", "top"]

# Choose which Django system checks to silence
# SILENCED_SYSTEM_CHECKS = [
#     "security.W004",
#     "security.W008",
#     "security.W009",
#     "security.W020",
# ]
# # security.W004: Disable HSTS with Azure domain; should enable for custom domain
# # security.W008: SSL termination and redirection by Azure
# # security.W009: SECRET_KEY is set in deployment
# # security.W020: ALLOWED_HOSTS is set in deployment
 