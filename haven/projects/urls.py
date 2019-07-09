from django.urls import path

from . import views


app_name = 'projects'

urlpatterns = [
    path('', views.ProjectList.as_view(), name='list'),
    path('new', views.ProjectCreate.as_view(), name='create'),

    path(
        '<int:pk>',
        views.ProjectDetail.as_view(),
        name='detail'
    ),

    path(
        '<int:pk>/edit',
        views.ProjectEdit.as_view(),
        name='edit'
    ),

    path(
        '<int:pk>/participants/',
        views.ProjectListParticipants.as_view(),
        name='list_participants'
    ),

    path(
        '<int:pk>/participants/edit',
        views.EditProjectListParticipants.as_view(),
        name='edit_participants'
    ),

    path(
        '<int:pk>/participants/add',
        views.ProjectAddUser.as_view(),
        name='add_user'
    ),

    path(
        '<int:pk>/datasets/',
        views.ProjectListDatasets.as_view(),
        name='list_datasets'
    ),

    path(
        '<int:pk>/datasets/new',
        views.ProjectCreateDataset.as_view(),
        name='add_dataset'
    ),

    path(
        '<int:pk>/work_packages/',
        views.ProjectListWorkPackages.as_view(),
        name='list_work_packages'
    ),

    path(
        '<int:pk>/work_packages/new',
        views.ProjectCreateWorkPackage.as_view(),
        name='add_work_package'
    ),

    path(
        '<int:project_pk>/work_packages/<int:pk>',
        views.WorkPackageDetail.as_view(),
        name='work_package_detail'
    ),

    path(
        '<int:project_pk>/work_packages/<int:pk>/classify',
        views.WorkPackageClassifyData.as_view(),
        name='classify_data'
    ),

    path(
        '<int:project_pk>/work_packages/<int:pk>/classify_delete',
        views.WorkPackageClassifyDelete.as_view(),
        name='classify_delete'
    ),

    path('<int:pk>/new_participant_autocomplete/',
         views.NewParticipantAutocomplete.as_view(),
         name='new_participant_autocomplete'
    ),
]
