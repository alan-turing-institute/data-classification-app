from django.db import models
from django.db.models import Q

from projects.roles import ProjectRole


class ProjectQuerySet(models.QuerySet):
    def get_visible_projects(self, user):
        if user.user_role.can_view_all_projects:
            return self
        else:
            return self.filter(
                Q(created_by=user) |
                Q(participants__user=user)
            ).distinct()

    def get_editable_projects(self, user):
        if user.user_role.can_edit_all_projects:
            return self
        else:
            return self.filter(
                Q(created_by=user) |
                Q(participants__user=user, participants__role__in=[
                    ProjectRole.PROJECT_MANAGER.value,
                    ProjectRole.INVESTIGATOR.value,
                ]))
