from django.urls import path

from haven.projects import views
import haven.projects.api.views  as api_views


app_name = "projects"

urlpatterns = [
    path("", views.ProjectList.as_view(), name="list"),
    path("new", views.ProjectCreate.as_view(), name="create"),
    path("programmes", views.ProgrammeList.as_view(), name="programmes"),
    path("<int:pk>", views.ProjectDetail.as_view(), name="detail"),
    path("<int:pk>/edit", views.ProjectEdit.as_view(), name="edit"),
    path("<int:pk>/history", views.ProjectHistory.as_view(), name="history"),
    path("<int:pk>/archive", views.ProjectArchive.as_view(), name="archive"),
    path(
        "<int:pk>/participants/edit",
        views.EditProjectListParticipants.as_view(),
        name="edit_participants",
    ),
    path("<int:pk>/participants/add", views.ProjectAddUser.as_view(), name="add_user"),
    path(
        "<int:project_pk>/participants/<int:pk>/edit",
        views.EditParticipant.as_view(),
        name="edit_participant",
    ),
    path(
        "<int:pk>/datasets/new",
        views.ProjectCreateDataset.as_view(),
        name="add_dataset",
    ),
    path(
        "<int:project_pk>/datasets/<int:pk>",
        views.ProjectDatasetDetail.as_view(),
        name="dataset_detail",
    ),
    path(
        "<int:project_pk>/datasets/<int:pk>/delete",
        views.ProjectDeleteDataset.as_view(),
        name="delete_dataset",
    ),
    path(
        "<int:project_pk>/datasets/<int:pk>/edit",
        views.ProjectEditDataset.as_view(),
        name="edit_dataset",
    ),
    path(
        "<int:project_pk>/datasets/<int:pk>/edit_dpr",
        views.ProjectEditDatasetDPR.as_view(),
        name="edit_dataset_dpr",
    ),
    path(
        "<int:pk>/work_packages/new",
        views.ProjectCreateWorkPackage.as_view(),
        name="add_work_package",
    ),
    path(
        "<int:project_pk>/work_packages/<int:pk>",
        views.WorkPackageDetail.as_view(),
        name="work_package_detail",
    ),
    path(
        "<int:project_pk>/work_packages/<int:pk>/delete",
        views.WorkPackageDelete.as_view(),
        name="work_package_delete",
    ),
    path(
        "<int:project_pk>/work_packages/<int:pk>/edit",
        views.WorkPackageEdit.as_view(),
        name="work_package_edit",
    ),
    path(
        "<int:project_pk>/work_packages/<int:pk>/classify",
        views.WorkPackageClassifyData.as_view(),
        name="classify_data",
    ),
    path(
        "<int:project_pk>/work_packages/<int:pk>/classify/<int:question_pk>",
        views.WorkPackageClassifyData.as_view(),
        name="classify_data",
    ),
    path(
        "<int:project_pk>/work_packages/<int:pk>/classify_results",
        views.WorkPackageClassifyResults.as_view(),
        name="classify_results",
    ),
    path(
        "<int:project_pk>/work_packages/<int:pk>/classify_clear",
        views.WorkPackageClear.as_view(),
        name="classify_clear",
    ),
    path(
        "<int:project_pk>/work_packages/<int:pk>/classify_delete",
        views.WorkPackageClassifyDelete.as_view(),
        name="classify_delete",
    ),
    path(
        "<int:project_pk>/work_packages/<int:pk>/classify_close",
        views.WorkPackageClassifyClose.as_view(),
        name="classify_close",
    ),
    path(
        "<int:project_pk>/work_packages/<int:pk>/classify_open",
        views.WorkPackageClassifyOpen.as_view(),
        name="classify_open",
    ),
    path(
        "<int:project_pk>/work_packages/<int:pk>/datasets/new",
        views.WorkPackageAddDataset.as_view(),
        name="work_package_add_dataset",
    ),
    path(
        "<int:project_pk>/work_packages/<int:pk>/datasets/edit",
        views.WorkPackageEditDatasets.as_view(),
        name="work_package_edit_datasets",
    ),
    path(
        "<int:project_pk>/work_packages/<int:pk>/participants/new",
        views.WorkPackageAddParticipant.as_view(),
        name="work_package_add_participant",
    ),
    path(
        "<int:project_pk>/work_packages/<int:pk>/participants/edit",
        views.WorkPackageEditParticipants.as_view(),
        name="work_package_edit_participants",
    ),
    path(
        "<int:project_pk>/work_packages/<int:pk>/participants/approve",
        views.WorkPackageApproveParticipants.as_view(),
        name="work_package_approve_participants",
    ),
    path(
        "<int:pk>/autocomplete_dpr/",
        views.AutocompleteDataProviderRepresentative.as_view(),
        name="autocomplete_dpr",
    ),
    path(
        "<int:pk>/autocomplete_new_participant/",
        views.AutocompleteNewParticipant.as_view(),
        name="autocomplete_new_participant",
    ),
    path(
        "autocomplete_programme/",
        views.AutocompleteProgramme.as_view(),
        name="autocomplete_programme",
    ),
    path(
        route="api/",
        view=api_views.ProjectListAPIView.as_view(),
        name="project_rest_api"
    ),
    path(
        route="api/<uuid:uuid>/",
        view=api_views.ProjectRetrieveAPIView.as_view(),
        name="project_rest_api"
    ),
]
