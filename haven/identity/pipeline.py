from functools import wraps

from django.conf import settings
from social_core.exceptions import AuthForbidden

from haven.identity.graph import user_client
from haven.identity.models import User
from haven.identity.roles import UserRole


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
    try:
        user.username = response['upn']
    except KeyError:
        # upn is not provided for AD guest users
        pass

    graph = user_client(user)
    graph_response = graph.get_me()
    if graph_response.ok:
        remote_email = graph_response.json().get('mail', '')
        if remote_email:
            user.email = remote_email

    user.save()


@azure_backend
def determine_role(backend, user, response, *args, **kwargs):
    """
    Social authentication pipeline

    Query the Graph API for user's groups and assign roles as appropriate.
    """
    graph = user_client(user)
    graph_response = graph.get_my_memberships()

    # Default user role to none
    role = UserRole.NONE

    # Preserve previous role unless System Manager
    if user.role and user.role != UserRole.SYSTEM_MANAGER.value:
        role = UserRole(user.role)

    # System Manager is only set by being a member of the appropriate group
    if graph_response.ok:
        groups = graph_response.json().get('value', [])
        # System Manager overrides any other permissions
        for group in groups:
            if 'displayName' in group and group['displayName'] == settings.SECURITY_GROUP_SYSTEM_MANAGERS:
                role = UserRole.SYSTEM_MANAGER
                break
        # If not System Manager, then Programme Manager overrides any other permissions
        for group in groups:
            if 'displayName' in group and group['displayName'] == settings.SECURITY_GROUP_PROGRAMME_MANAGERS:
                role = UserRole.PROGRAMME_MANAGER
                break

    user.set_role(role)


@azure_backend
def find_existing_user(backend, user, response, *args, **kwargs):
    """
    Look up an existing user by UPN / username and load them
    into the pipeline

    """
    if user:
        # Normally, the user has already been loaded by the previous step in the pipeline, by
        # matching the 'sub' claim to the social_auth_usersocialauth table
        return

    # User has not logged in before
    # Different claims are provided depending on what type of user is in AD (e.g. Member or Guest)
    username = response.get('unique_name') or response.get('upn')
    if not username:
        raise AuthForbidden('azuread-tenant-oauth2')

    try:
        user = User.objects.get(username=username)
        return {'user': user}
    except User.DoesNotExist:
        # User hasn't logged in, doesn't already exist. A later pipeline step will create a new user
        pass
