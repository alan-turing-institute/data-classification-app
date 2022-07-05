from django import template
from django.template.defaultfilters import stringfilter

from haven.identity.roles import UserRole


register = template.Library()


@register.filter
@stringfilter
def role_display(role):
    return dict(UserRole.choices()).get(role, "")


@register.filter
def auth_display(backend):
    return settings.SOCIAL_AUTH_BACKEND_DISPLAY_NAMES.get(backend, backend)
