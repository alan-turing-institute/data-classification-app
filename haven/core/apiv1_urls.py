"""Called from haven.urls URLConf like so:
    path("api/", include("haven.core.apiv1_urls", namespace="api")),
"""

from django.urls import path

from haven.projects.api import views as project_views

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
]