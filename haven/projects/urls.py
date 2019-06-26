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
        '<int:pk>/classify',
        views.ProjectClassifyData.as_view(),
        name='classify_data'
    ),

    path(
        '<int:pk>/classify_delete',
        views.ProjectClassifyDelete.as_view(),
        name='classify_delete'
    ),

    path('<int:pk>/new_participant_autocomplete/',
         views.NewParticipantAutocomplete.as_view(),
         name='new_participant_autocomplete'
    ),
]
