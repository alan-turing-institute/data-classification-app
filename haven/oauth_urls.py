from django.contrib.auth.decorators import user_passes_test
from django.urls import re_path
from oauth2_provider import views
from oauth2_provider.urls import base_urlpatterns, oidc_urlpatterns

from haven.api.views import (
    CustomApplicationRegistration,
    CustomClientApplicationUpdate,
)


app_name = "oauth2_provider"


def can_access_oauth_application_views(user):
    """
    Function which returns a boolean for where or not user should be able to access the application
    views provided by django-oauth-toolkit
    """
    return user.is_authenticated and (
        user.is_superuser or user.system_permissions.can_manage_applications
    )


management_urlpatterns = [
    # Application management views
    # Applying permissions checks here with user_passes_test decorator to avoid having to 
    # inherit from multiple 3rd party classes
    re_path(
        r"^applications/$",
        user_passes_test(can_access_oauth_application_views)(views.ApplicationList.as_view()),
        name="list",
    ),
    re_path(
        r"^applications/register/$",
        user_passes_test(can_access_oauth_application_views)(
            CustomApplicationRegistration.as_view()
        ),
        name="register",
    ),
    re_path(
        r"^applications/(?P<pk>[\w-]+)/$",
        user_passes_test(can_access_oauth_application_views)(views.ApplicationDetail.as_view()),
        name="detail",
    ),
    re_path(
        r"^applications/(?P<pk>[\w-]+)/delete/$",
        user_passes_test(can_access_oauth_application_views)(views.ApplicationDelete.as_view()),
        name="delete",
    ),
    re_path(
        r"^applications/(?P<pk>[\w-]+)/update/$",
        user_passes_test(can_access_oauth_application_views)(
            CustomClientApplicationUpdate.as_view()
        ),
        name="update",
    ),
]


urlpatterns = base_urlpatterns + management_urlpatterns + oidc_urlpatterns
