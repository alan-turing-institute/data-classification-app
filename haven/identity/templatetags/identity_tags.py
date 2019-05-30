from django import template
from django.template.defaultfilters import stringfilter

from haven.identity.roles import UserRole


register = template.Library()


@register.filter
@stringfilter
def role_display(role):
    return dict(UserRole.choices()).get(role, '')


@register.filter
def has_role(users, role):
    return users.filter(role=role)
