from django.db.models import Q
from django.contrib.auth.models import UserManager


class CustomUserManager(UserManager):
    """UserManager with custom QuerySet method"""

    def get_visible_users(self, user):
        """
        Return QuerySet of objects the specified user is permitted to view
        """
        default_query_set = self.get_queryset()
        if user.system_permissions.can_view_all_users:
            return default_query_set
        else:
            return default_query_set.filter(
                Q(created_by=user)
            ).distinct()

    def get_by_natural_key(self, username):
        """
        Return the User with this matching username. If there is no exact match, try a case-insensitive match
        """
        try:
            # Look for an exact username match
            return self.get(**{self.model.USERNAME_FIELD: username})
        except self.model.DoesNotExist:
            # If no exact username match was found, look for a case-insensitive username match
            case_insensitive_username_field = '{}__iexact'.format(self.model.USERNAME_FIELD)
            return self.get(**{case_insensitive_username_field: username})
