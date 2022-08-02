from django.urls import path

from haven.projects import views


app_name = "projects"

urlpatterns = [
    path("", views.ProjectList.as_view(), name="list"),
    path("new", views.ProjectCreate.as_view(), name="create"),
    path("programmes", views.ProgrammeList.as_view(), name="programmes"),
    path("<slug:uuid>", views.ProjectDetail.as_view(), name="detail"),
    path("<slug:uuid>/edit", views.ProjectEdit.as_view(), name="edit"),
    path("<slug:uuid>/history", views.ProjectHistory.as_view(), name="history"),
    path("<slug:uuid>/archive", views.ProjectArchive.as_view(), name="archive"),
    path(
        "<slug:uuid>/participants/edit",
        views.EditProjectListParticipants.as_view(),
        name="edit_participants",
    ),
    path("<slug:uuid>/participants/add", views.ProjectAddUser.as_view(), name="add_user"),
    path(
        "<slug:project__uuid>/participants/<slug:uuid>/edit",
        views.EditParticipant.as_view(),
        name="edit_participant",
    ),
    path(
        "<slug:uuid>/datasets/new",
        views.ProjectCreateDataset.as_view(),
        name="add_dataset",
    ),
    path(
        "<slug:project__uuid>/datasets/<slug:uuid>",
        views.ProjectDatasetDetail.as_view(),
        name="dataset_detail",
    ),
    path(
        "<slug:project__uuid>/datasets/<slug:uuid>/delete",
        views.ProjectDeleteDataset.as_view(),
        name="delete_dataset",
    ),
    path(
        "<slug:project__uuid>/datasets/<slug:uuid>/edit",
        views.ProjectEditDataset.as_view(),
        name="edit_dataset",
    ),
    path(
        "<slug:project__uuid>/datasets/<slug:uuid>/edit_dpr",
        views.ProjectEditDatasetDPR.as_view(),
        name="edit_dataset_dpr",
    ),
    path(
        "<slug:uuid>/work_packages/new",
        views.ProjectCreateWorkPackage.as_view(),
        name="add_work_package",
    ),
    path(
        "<slug:project__uuid>/work_packages/<slug:uuid>",
        views.WorkPackageDetail.as_view(),
        name="work_package_detail",
    ),
    path(
        "<slug:project__uuid>/work_packages/<slug:uuid>/delete",
        views.WorkPackageDelete.as_view(),
        name="work_package_delete",
    ),
    path(
        "<slug:project__uuid>/work_packages/<slug:uuid>/edit",
        views.WorkPackageEdit.as_view(),
        name="work_package_edit",
    ),
    path(
        "<slug:project__uuid>/work_packages/<slug:uuid>/classify",
        views.WorkPackageClassifyData.as_view(),
        name="classify_data",
    ),
    path(
        "<slug:project__uuid>/work_packages/<slug:uuid>/classify/<int:question_pk>",
        views.WorkPackageClassifyData.as_view(),
        name="classify_data",
    ),
    path(
        "<slug:project__uuid>/work_packages/<slug:uuid>/classify_results",
        views.WorkPackageClassifyResults.as_view(),
        name="classify_results",
    ),
    path(
        "<slug:project__uuid>/work_packages/<slug:uuid>/classify_clear",
        views.WorkPackageClear.as_view(),
        name="classify_clear",
    ),
    path(
        "<slug:project__uuid>/work_packages/<slug:uuid>/classify_delete",
        views.WorkPackageClassifyDelete.as_view(),
        name="classify_delete",
    ),
    path(
        "<slug:project__uuid>/work_packages/<slug:uuid>/classify_close",
        views.WorkPackageClassifyClose.as_view(),
        name="classify_close",
    ),
    path(
        "<slug:project__uuid>/work_packages/<slug:uuid>/classify_open",
        views.WorkPackageClassifyOpen.as_view(),
        name="classify_open",
    ),
    path(
        "<slug:project__uuid>/work_packages/<slug:uuid>/datasets/new",
        views.WorkPackageAddDataset.as_view(),
        name="work_package_add_dataset",
    ),
    path(
        "<slug:project__uuid>/work_packages/<slug:uuid>/datasets/edit",
        views.WorkPackageEditDatasets.as_view(),
        name="work_package_edit_datasets",
    ),
    path(
        "<slug:project__uuid>/work_packages/<slug:uuid>/participants/new",
        views.WorkPackageAddParticipant.as_view(),
        name="work_package_add_participant",
    ),
    path(
        "<slug:project__uuid>/work_packages/<slug:uuid>/participants/edit",
        views.WorkPackageEditParticipants.as_view(),
        name="work_package_edit_participants",
    ),
    path(
        "<slug:project__uuid>/work_packages/<slug:uuid>/participants/approve",
        views.WorkPackageApproveParticipants.as_view(),
        name="work_package_approve_participants",
    ),
    path(
        "<slug:uuid>/autocomplete_dpr/",
        views.AutocompleteDataProviderRepresentative.as_view(),
        name="autocomplete_dpr",
    ),
    path(
        "<slug:uuid>/autocomplete_new_participant/",
        views.AutocompleteNewParticipant.as_view(),
        name="autocomplete_new_participant",
    ),
    path(
        "autocomplete_programme/",
        views.AutocompleteProgramme.as_view(),
        name="autocomplete_programme",
    ),
]
