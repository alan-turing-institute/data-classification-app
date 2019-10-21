from django.db import models
from django.db.models import Q

from projects.roles import ProjectRole


class ProjectQuerySet(models.QuerySet):
    def get_visible_projects(self, user):
        qs = self.filter(archived=False)
        if not user.user_role.can_view_all_projects:
            qs = qs.filter(
                Q(created_by=user) |
                Q(participants__user=user)
            ).distinct()
        return qs

    def get_editable_projects(self, user):
        qs = self.filter(archived=False)
        if not user.user_role.can_view_all_projects:
            qs = qs.filter(
                Q(created_by=user) |
                Q(participants__user=user, participants__role__in=[
                    ProjectRole.PROJECT_MANAGER.value,
                    ProjectRole.INVESTIGATOR.value,
                ]))
        return qs
