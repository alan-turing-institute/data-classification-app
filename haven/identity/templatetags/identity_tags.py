from django import template
from django.template.defaultfilters import stringfilter

from identity.roles import UserRole

register = template.Library()


@register.filter
@stringfilter
def role_display(role):
    return dict(UserRole.choices()).get(role, '')

