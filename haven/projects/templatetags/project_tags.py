from django import template
from django.template.defaultfilters import stringfilter

from ..roles import ProjectRole


register = template.Library()


@register.filter
@stringfilter
def project_role_display(role):
    return dict(ProjectRole.choices()).get(role, '')


@register.filter
def tier(tier):
    if tier is None:
        return '?'
    else:
        return str(tier)


@register.filter
def project_role(user, project):
    role = user.project_participation_role(project)
    return  project_role_display(role.value if role else None)
