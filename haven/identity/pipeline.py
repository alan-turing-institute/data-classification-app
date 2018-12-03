from functools import wraps

from django.conf import settings
from requests_oauthlib import OAuth2Session

from identity.models import User
from identity.roles import UserRole


GRAPH_URL = 'https://graph.microsoft.com/v1.0/'


def _authenticated_client(user):
    token = user.social_auth.first().extra_data
    return OAuth2Session(token=token)


def azure_backend(fn):
    @wraps(fn)
    def _inner(backend, *args, **kwargs):
        if backend.name == 'azuread-tenant-oauth2':
            return fn(backend, *args, **kwargs)
    return _inner


@azure_backend
def user_fields(backend, user, response, *args, **kwargs):
    """
    Social authentication pipeline

    Convert values from oauth2 to user fields
    """
    user.username = response['upn']

    graph = _authenticated_client(user)
    me = graph.get(GRAPH_URL + 'me')
    if me.ok:
        user.email = me.json().get('mail', '')

    user.save()


@azure_backend
def determine_role(backend, user, response, *args, **kwargs):
    """
    Social authentication pipeline

    Query the Graph API for user's groups and assign roles as appropriate.
    """
    graph = _authenticated_client(user)
    response = graph.get(GRAPH_URL + 'me/memberOf')

    if response.ok:
        groups = response.json().get('value', [])
        for group in groups:
            if group['displayName'] == settings.SYS_CONTROLLER_GROUP_NAME:
                user.set_role(UserRole.SYSTEM_CONTROLLER)
                break


@azure_backend
def find_existing_user(backend, user, response, *args, **kwargs):
    if user:
        return {}

    try:
        user = User.objects.get(username=response['upn'])
        return {'user': user}
    except User.ObjectDoesNotExist:
        return {}
