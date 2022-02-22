from configurations import values

class RemoteUserMixin(object):
    """Mixin for configuring the application to make use of external
    authentication sources such as Authelia.
    See https://docs.djangoproject.com/en/4.0/howto/auth-remote-user/
    """
    @property
    def MIDDLEWARE(self):
        return [
            "haven.identity.auth.middleware.HttpRemoteUserMiddleware"
        ] + super(RemoteUserMixin, self).MIDDLEWARE

    @property
    def AUTHENTICATION_BACKENDS(self):
        return [
            "haven.identiry.auth.backends.RemoteExtendedUserBackend",
        ] + super(RemoteUserMixin, self).AUTHENTICATION_BACKENDS

    # Logout from authelia after logout from Django app
    @property
    def LOGOUT_REDIRECT_URL(self):
        return "https://auth." + super(RemoteUserMixin, self).BASE_DOMAIN + "/logout"

class LocalUserMixin(object):
    """Enable login with local user accounts"""
    @property
    def AUTHENTICATION_BACKENDS(self):
        return super(LocalUserMixin, self).AUTHENTICATION_BACKENDS + [
            "django.contrib.auth.backends.ModelBackend",
        ]

class SocialAuthMixin(object):
    """Enable login with OAuth2 through a social provider
    like GitHub, ORCID, or Google"""

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

    AUTH_BACKEND_DISPLAY_NAMES = {}


class AzureUserMixin(SocialAuthMixin):
    LOGIN_URL = "/auth/login/azuread-tenant-oauth2/"

    @property
    def AUTHENTICATION_BACKENDS(self):
        return [
            "haven.identity.backends.CustomAzureOAuth2Backend",
        ] + super(AzureUserMixin, self).AUTHENTICATION_BACKENDS

    @property
    def AUTH_BACKEND_DISPLAY_NAMES(self):
        display_names = super(AzureUserMixin, self).AUTH_BACKEND_DISPLAY_NAMES
        display_names["azure-ad-tenant"] = "Azure"
        return display_names

    SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY = values.Value(environ_prefix="")
    SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET = values.Value(environ_prefix="")
    SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID = values.Value(environ_prefix="")
    SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_RESOURCE = "https://graph.microsoft.com"

    # Haven specific Azure AD settings
    SECURITY_GROUP_SYSTEM_MANAGERS = values.Value(
        "SG SHM Programme Managers",
        environ_prefix=""
    )
    SECURITY_GROUP_PROGRAMME_MANAGERS = values.Value(
        "SG SHM Programme Managers",
        environ_prefix=""
    )
    SECURITY_GROUP_PROJECT_MANAGERS = values.Value(
        "SG SHM Project Managers",
        environ_prefix=""
    )
    AD_RESEARCH_USER_DN = "CN=%(cn)s,OU=Safe Haven Research Users,DC=dsgroupdev,DC=co,DC=uk"
    AD_USER_OBJECT_CLASSES = ["user", "organizationalPerson", "person", "top"]


class GitHubUserMixin(SocialAuthMixin):

    @property
    def AUTHENTICATION_BACKENDS(self):
        return [
            "social_core.backends.github.GithubOAuth2",
        ] + super(GitHubUserMixin, self).AUTHENTICATION_BACKENDS

    @property
    def AUTH_BACKEND_DISPLAY_NAMES(self):
        display_names = super(GitHubUserMixin, self).AUTH_BACKEND_DISPLAY_NAMES
        display_names["github"] = "GitHub"
        return display_names

    SOCIAL_AUTH_GITHUB_KEY = values.Value(environ_prefix="")
    SOCIAL_AUTH_GITHUB_SECRET = values.Value(environ_prefix="")

class ORCIDSandboxUserMixin(SocialAuthMixin):

    @property
    def AUTHENTICATION_BACKENDS(self):
        return [
            "social_core.backends.orcid.ORCIDMemberOAuth2Sandbox",
        ] + super(ORCIDSandboxUserMixin, self).AUTHENTICATION_BACKENDS

    @property
    def AUTH_BACKEND_DISPLAY_NAMES(self):
        display_names = super(ORCIDSandboxUserMixin, self).AUTH_BACKEND_DISPLAY_NAMES
        display_names["orcid-sandbox"] = "ORCID"
        return display_names

    SOCIAL_AUTH_ORCID_SANDBOX_KEY = values.Value(environ_prefix="")
    SOCIAL_AUTH_ORCID_SANDBOX_SECRET = values.Value(environ_prefix="")


class ORCIDUserMixin(SocialAuthMixin):

    @property
    def AUTHENTICATION_BACKENDS(self):
        return [
            "social_core.backends.orcid.ORCIDMemberOAuth2",
        ] + super(ORCIDUserMixin, self).AUTHENTICATION_BACKENDS

    @property
    def AUTH_BACKEND_DISPLAY_NAMES(self):
        display_names = super(ORCIDUserMixin, self).AUTH_BACKEND_DISPLAY_NAMES
        display_names["orcid"] = "ORCID"
        return display_names

    SOCIAL_AUTH_ORCID_KEY = values.Value(environ_prefix="")
    SOCIAL_AUTH_ORCID_SECRET = values.Value(environ_prefix="")