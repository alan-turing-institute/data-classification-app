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
        "projects/<slug:project__uuid>/work_packages",
        views.WorkPackageListAPIView.as_view(),
        name="project_work_package_list",
    ),
    path(
        "projects/<slug:project__uuid>/work_packages/<slug:uuid>",
        views.WorkPackageDetailAPIView.as_view(),
        name="project_work_package_detail",
    ),
    path(
        # Notice the plural `projects__uuid` rather than `project__uuid`
        # Work packages have a fk to project whereas datasets have a M2M relation with projects
        "projects/<slug:projects__uuid>/datasets",
        views.DatasetListAPIView.as_view(),
        name="project_dataset_list",
    ),
    path(
        "projects/<slug:projects__uuid>/datasets/<slug:uuid>",
        views.DatasetDetailAPIView.as_view(),
        name="project_dataset_detail",
    ),
    path(
        "projects/<slug:projects__uuid>/work_packages/<slug:work_packages__uuid>/datasets",
        views.DatasetListAPIView.as_view(),
        name="project_work_package_dataset_list",
    ),
    path(
        "projects/<slug:projects__uuid>/work_packages/"
        "<slug:work_packages__uuid>/datasets/<slug:uuid>",
        views.DatasetDetailAPIView.as_view(),
        name="project_work_package_dataset_detail",
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
    path(
        "work_packages/<slug:work_packages__uuid>/datasets",
        views.DatasetListAPIView.as_view(),
        name="work_package_dataset_list",
    ),
    path(
        "work_packages/<slug:work_packages__uuid>/datasets/<slug:uuid>",
        views.DatasetDetailAPIView.as_view(),
        name="work_package_dataset_detail",
    ),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
