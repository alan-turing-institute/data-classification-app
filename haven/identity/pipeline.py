import logging


logger = logging.getLogger(__name__)


def user_fields(backend, user, response, *args, **kwargs):
    """
    Social authentication pipeline

    Convert values from oauth2 to user fields
    """
    if backend.name == 'azuread-tenant-oauth2':
        user.username = response['upn']
        user.save()
