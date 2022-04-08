from django import template
from django.template.defaultfilters import stringfilter

from haven.projects.roles import ProjectRole


register = template.Library()


@register.filter
@stringfilter
def project_role_display(role):
    try:
        return ProjectRole.display_name(role)
    except KeyError:
        return ""


@register.filter
def tier(tier):
    if tier is None:
        return "?"
    else:
        return str(tier)


@register.filter
def project_participation_role(user, project):
    role = user.project_participation_role(project)
    return project_role_display(role.value if role else None)
