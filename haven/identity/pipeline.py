from django.conf import settings
from requests_oauthlib import OAuth2Session

from identity.roles import UserRole


def user_fields(backend, user, response, *args, **kwargs):
    """
    Social authentication pipeline

    Convert values from oauth2 to user fields
    """
    if backend.name == 'azuread-tenant-oauth2':
        user.username = response['upn']
        user.save()


def determine_role(backend, user, response, *args, **kwargs):
    token = user.social_auth.first().extra_data

    graph_client = OAuth2Session(token=token)

    response = graph_client.get('https://graph.microsoft.com/v1.0/me/memberOf')

    if response.ok:
        groups = response.json().get('value', [])

        for group in groups:
            if group['displayName'] == settings.SYS_CONTROLLER_GROUP_NAME:
                user.set_role(UserRole.SYSTEM_CONTROLLER)
