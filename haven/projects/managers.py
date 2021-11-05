from django.db import models as db_models
from django.db.models import Q

from haven.projects import models
from haven.projects.roles import ProjectRole


class ProjectQuerySet(db_models.QuerySet):
    def get_visible_projects(self, user):
        qs = self.filter(archived=False)
        if not user.system_permissions.can_view_all_projects:
            qs = qs.filter(Q(created_by=user) | Q(participants__user=user)).distinct()
        return qs

    def get_editable_projects(self, user):
        qs = self.filter(archived=False)
        if not user.system_permissions.can_edit_all_projects:
            qs = qs.filter(
                Q(created_by=user)
                | Q(
                    participants__user=user,
                    participants__role__in=[
                        ProjectRole.PROJECT_MANAGER.value,
                        ProjectRole.INVESTIGATOR.value,
                    ],
                )
            )
        return qs


class WorkPackageQuerySet(db_models.QuerySet):
    def filter_by_permission(self, permission, exclude=False):
        permission_dict = models.WorkPackage._get_permission_dict(permission)
        statuses = [k for k, v in permission_dict.items() if v != exclude]
        return self.filter(status__in=statuses)
