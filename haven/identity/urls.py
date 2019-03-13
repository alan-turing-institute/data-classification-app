from django.urls import path

from . import views


app_name = 'identity'

urlpatterns = [
    path('', views.UserList.as_view(), name='list'),
    path('new', views.UserCreate.as_view(), name='add_user'),

    path(
        '<int:pk>/edit',
        views.UserEdit.as_view(),
        name='edit_user',
    ),
]
