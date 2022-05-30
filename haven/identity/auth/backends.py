from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.backends import RemoteUserBackend

from haven.identity.roles import UserRole

class RemoteExtendedUserBackend(RemoteUserBackend):
    """
    This backend can be used in conjunction with the ``RemoteUserMiddleware``
    to handle authentication outside Django and update local user with external information
    (name, email and groups).

    Extends RemoteUserBackend (it creates the Django user if it does not exist,
    as explained here: https://github.com/django/django/blob/main/django/contrib/auth/backends.py#L167),
    updating the user with the information received from the remote headers.

    Django user is only added to groups that already exist on the database (no groups are created).
    A settings variable can be used to exclude some groups when updating the user.
    """

    excluded_groups = set()
    if hasattr(settings, 'REMOTE_AUTH_BACKEND_EXCLUDED_GROUPS'):
        excluded_groups = set(settings.REMOTE_AUTH_BACKEND_EXCLUDED_GROUPS)

    # Warning: possible security breach if reverse proxy does not set
    # these variables EVERY TIME it hits this Django application (and REMOTE_USER variable).
    # See https://docs.djangoproject.com/en/4.0/howto/auth-remote-user/#configuration
    header_name = 'HTTP_REMOTE_NAME'
    header_groups = 'HTTP_REMOTE_GROUPS'
    header_email = 'HTTP_REMOTE_EMAIL'

    def authenticate(self, request, remote_user):
        user = super().authenticate(request, remote_user)

        # original authenticate calls configure_user only
        # when user is created. We need to call this method every time
        # the user is authenticated in order to update its data.
        if user:
            self.configure_user(request, user)
        return user

    def configure_user(self, request, user):
        """
        Complete the user from extra request.META information.
        """
        if self.header_name in request.META:
            user.last_name = request.META[self.header_name]

        if self.header_email in request.META:
            user.email = request.META[self.header_email]

        if self.header_groups in request.META:
            self.update_groups(user, request.META[self.header_groups])

        if self.user_has_to_be_staff(user):
            user.is_staff = True

        user.save()
        return user

    def user_has_to_be_staff(self, user):
        return True

    def update_user_role(self, user, target_group_names):
        # Is the user a system manager?
        if settings.SYSTEM_MANAGER_LDAP_GROUP in target_group_names:
            user.role = UserRole.SYSTEM_MANAGER.value
            user.save()
            return target_group_names - set([settings.SYSTEM_MANAGER_LDAP_GROUP])
        # Is the user a programme manager?
        elif settings.PROGRAMME_MANAGER_LDAP_GROUP in list(target_group_names):
            user.role = UserRole.PROGRAMME_MANAGER.value
            user.save()
            return target_group_names - set([settings.SYSTEM_MANAGER_LDAP_GROUP])
        else:
            return target_group_names

    def update_groups(self, user, remote_groups):
        """
        Synchronizes groups the user belongs to with remote information.

        Groups (existing django groups or remote groups) on excluded_groups are completely ignored.
        No group will be created on the django database.

        Disclaimer: this method is strongly inspired by the LDAPBackend from django-auth-ldap.
        """
        current_group_names = frozenset(
            user.groups.values_list("name", flat=True).iterator()
        )
        preserved_group_names = current_group_names.intersection(self.excluded_groups)
        current_group_names = current_group_names - self.excluded_groups

        target_group_names = frozenset(
            [x for x in map(self.clean_groupname, remote_groups.split(',')) if x is not None]
        )
        target_group_names = target_group_names - self.excluded_groups
        target_group_names = self.update_user_role(user, target_group_names)

        if target_group_names != current_group_names:
            target_group_names = target_group_names.union(preserved_group_names)
            existing_groups = list(
                Group.objects.filter(name__in=target_group_names).iterator()
            )
            user.groups.set(existing_groups)
        return

    def clean_groupname(self, groupname):
        """
        Perform any cleaning on the "groupname" prior to using it.
        Return the cleaned groupname.
        """
        return groupname
