from django.contrib.auth.models import AbstractUser
from django.db import models

from .roles import ProjectRole, UserRole


class User(AbstractUser):
    """
    Represents a user that can log in to the system
    """
    role = models.CharField(
        max_length=50,
        choices=UserRole.choices(),
        blank=True,
        help_text="The user's role in the system"
    )

    # No created_at field here since `AbstractUser` already stores this
    created_by = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        related_name='+',
        help_text='User who created this user',
    )

    @property
    def user_role(self):
        if self.is_superuser:
            return UserRole.SUPERUSER
        return UserRole(self.role)

    def can_add_user_to_project(self, project):
        return bool(self.creatable_roles_for_project(project))

    def is_project_admin(self, project):
        return (self.is_superuser or
                self.user_role is UserRole.SYSTEM_CONTROLLER or
                project.created_by == self)

    def creatable_roles_for_project(self, project):
        """
        Roles this user is allowed to create on the given project
        """
        if self.is_project_admin(project):
            return ProjectRole.ALL
        else:
            role = project.user_role(self)
            if role:
                return ProjectRole.ALLOWED_CREATIONS[role]

        return []

    def can_list_participants(self, project):
        return self.is_project_admin(project)
