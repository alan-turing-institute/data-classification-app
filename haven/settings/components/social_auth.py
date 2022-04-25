import environ


env = environ.Env()

provider_dictionary = {
    "github": {
        "backend": "social_core.backends.github.GithubOAuth2",
        "display_name": "GitHub"
    },
    "orcid-sandbox": {
        "backend": "social_core.backends.orcid.ORCIDOAuth2Sandbox",
        "display_name": "ORCID Sandbox"
    },
    "azure-ad-tenant": {
        "backend": "haven.identity.backends.CustomAzureOAuth2Backend",
        "display_name": "Azure AD"
    }
}

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

SOCIAL_AUTH_GITHUB_KEY = env.str("SOCIAL_AUTH_GITHUB_KEY", default="")
SOCIAL_AUTH_GITHUB_SECRET = env.str("SOCIAL_AUTH_GITHUB_SECRET", default="")

SOCIAL_AUTH_ORCID_SANDBOX_KEY = env.str("SOCIAL_AUTH_ORCID_SANDBOX_KEY", default="")
SOCIAL_AUTH_ORCID_SANDBOX_SECRET = env.str("SOCIAL_AUTH_ORCID_SANDBOX_SECRET", default="")

SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY = env.str("AZUREAD_OAUTH2_KEY", default="")
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET = env.str("AZUREAD_OAUTH2_SECRET", default="")
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID = env.str(
    "AZUREAD_OAUTH2_TENANT_ID", default=""
)
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_RESOURCE = "https://graph.microsoft.com"
# Haven specific Azure AD settings
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