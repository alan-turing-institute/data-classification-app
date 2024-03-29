from django.urls import path

from haven.identity import views


app_name = "identity"

urlpatterns = [
    path("", views.UserList.as_view(), name="list"),
    path("new", views.UserCreate.as_view(), name="add_user"),
    path("import", views.ImportUsers.as_view(), name="import_users"),
    path("export", views.ExportUsers.as_view(), name="export_users"),
    path(
        "<slug:uuid>/edit",
        views.UserEdit.as_view(),
        name="edit_user",
    ),
]
