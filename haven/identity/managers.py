from django.db.models import Q
from django.contrib.auth.models import UserManager

class CustomUserManager(UserManager):
    """UserManager with custom QuerySet method"""

    def get_visible_users(self, user):
        """
        Return QuerySet of objects the specified user is permitted to view
        """
        default_query_set = self.get_queryset()
        if user.user_role.can_view_all_users:
            return default_query_set
        else:
            return default_query_set.filter(
                Q(created_by=user)
            ).distinct()
