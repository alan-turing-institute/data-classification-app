from functools import wraps

from django.conf import settings
from social_core.exceptions import AuthForbidden

from .graph import user_client
from .models import User
from .roles import UserRole


def azure_backend(fn):
    """
    Ensure a pipeline function only applies to Azure
    """
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

    graph = user_client(user)
    graph_response = graph.get_me()
    if graph_response.ok:
        user.email = graph_response.json().get('mail', '')

    user.save()


@azure_backend
def determine_role(backend, user, response, *args, **kwargs):
    """
    Social authentication pipeline

    Query the Graph API for user's groups and assign roles as appropriate.
    """
    graph = user_client(user)
    graph_response = graph.get_my_memberships()

    role = UserRole.NONE
    if graph_response.ok:
        groups = graph_response.json().get('value', [])
        for group in groups:
            if group['displayName'] == settings.SYS_CONTROLLER_GROUP_NAME:
                role = UserRole.SYSTEM_MANAGER
                break

    user.set_role(role)


@azure_backend
def find_existing_user(backend, user, response, *args, **kwargs):
    """
    Look up an existing user by UPN / username and load them
    into the pipeline
    """
    if not user:
        try:
            user = User.objects.get(username=response['upn'])
            return {'user': user}
        except User.DoesNotExist:
            pass
        # A missing upn key likely indicates log in from a personal account
        except KeyError:
            raise AuthForbidden('azuread-tenant-oauth2')
