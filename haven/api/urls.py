from django.urls import include, path

from haven.api import views


app_name = "api"


urlpatterns = [
    path("datasets", views.DatasetListAPIView.as_view(), name="dataset_list"),
    path(
        "datasets/<slug:uuid>",
        views.DatasetDetailAPIView.as_view(),
        name="dataset_detail",
    ),
    path("projects", views.ProjectListAPIView.as_view(), name="project_list"),
    path(
        "projects/<slug:uuid>",
        views.ProjectDetailAPIView.as_view(),
        name="project_detail",
    ),
    path(
        "work_packages",
        views.WorkPackageListAPIView.as_view(),
        name="work_package_list",
    ),
    path(
        "work_packages/<slug:uuid>",
        views.WorkPackageDetailAPIView.as_view(),
        name="work_package_detail",
    ),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
