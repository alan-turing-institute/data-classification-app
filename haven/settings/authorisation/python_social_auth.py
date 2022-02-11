

from haven.settings.authorisation.backends.azure_ad_tenant import AUTH_DISPLAY_NAME


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

AUTH_DISPLAY_NAMES = {}