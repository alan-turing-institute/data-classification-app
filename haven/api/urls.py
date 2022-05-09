from django.urls import include, path

from haven.api import views


app_name = "api"


urlpatterns = [
    path("datasets", views.DatasetListAPIView.as_view(), name="dataset_list"),
    path("datasets/<slug:uuid>", views.DatasetDetailAPIView.as_view(), name="dataset_detail"),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
