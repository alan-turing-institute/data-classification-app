from functools import wraps

from django.conf import settings
from social_core.exceptions import AuthForbidden

from .graph import user_client
from .models import User
from .roles import UserRole

from django.contrib.auth.models import Group


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

    new_django_groups = set()

    # Get user's current Django group memberships
    current_django_groups = set(g.name for g in user.groups.all())

    # Get user's new group memberships based on Graph group memberships
    if graph_response.ok:
        graph_groups = graph_response.json().get('value', [])
        permission_group_dict = UserRole.security_groups()
        # System Manager overrides any other permissions
        for group in graph_groups:
            if 'displayName' in group:
                group_name = group['displayName']
                if group_name in permission_group_dict:
                    permission_group = permission_group_dict[group_name]
                    new_django_groups.add(permission_group)

    # Add user to Django groups they need to be added to
    for group_name in new_django_groups - current_django_groups:
        group, created = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)

    # Remove user from Django groups they need be removed from
    for group_name in current_django_groups - new_django_groups:
        group = Group.objects.get(name=group_name)
        user.groups.remove(group)

    # Set user's overall membership
    if UserRole.SYSTEM_MANAGER.value in new_django_groups:
        role = UserRole.SYSTEM_MANAGER
    elif UserRole.PROGRAMME_MANAGER.value in new_django_groups:
        role = UserRole.PROGRAMME_MANAGER
    elif UserRole.PROJECT_MANAGER.value in new_django_groups:
        role = UserRole.PROJECT_MANAGER
    else:
        role = UserRole.NONE
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
