"""Called from haven.urls URLConf like so:
    path("api/", include("haven.core.apiv1_urls", namespace="api")),
"""

from django.urls import path

from haven.projects.api import views as project_views
from haven.identity.api import views as identity_views

app_name = "apiv1"

urlpatterns = [
    # {% url "api:projects" %}
    path(
        route="projects/",
        view=project_views.ProjectListAPIView.as_view(),
        name="projects"
    ),
    # {% url "api:projects" project.uuid %}
    path(
        route="projects/<uuid:uuid>/",
        view=project_views.ProjectRetrieveAPIView.as_view(),
        name="projects"
    ),
    # {% url "api:users" %}
    path(
        route="users/",
        view=identity_views.UserListAPIView.as_view(),
        name="users"
    ),
    # {% url "api:users" user.uuid %}
    path(
        route="users/<uuid:uuid>/",
        view=identity_views.UserResourceAPIView.as_view(),
        name="users"
    ),
]