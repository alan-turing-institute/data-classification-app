from django import template
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.template import defaulttags
from django.urls import resolve


register = template.Library()


class UrlCheckNode(template.Node):
    def __init__(self, wrapped_node):
        self.wrapped_node = wrapped_node

    def render(self, context):
        result = self.wrapped_node.render(context)
        if self.wrapped_node.asvar:
            url = context[self.wrapped_node.asvar]
        else:
            url = result

        match = resolve(url)
        view_func = match.func
        if hasattr(view_func, 'view_class'):
            view = view_func.view_class(**view_func.view_initkwargs)
            view.request = context['request']
            view.args = match.args
            view.kwargs = match.kwargs
            if isinstance(view, LoginRequiredMixin):
                if not view.request.user.is_authenticated:
                    url = None
            if isinstance(view, PermissionRequiredMixin):
                if not view.has_permission():
                    url = None
            if isinstance(view, UserPassesTestMixin):
                if not view.get_test_func()():
                    url = None

        if self.wrapped_node.asvar:
            context[self.wrapped_node.asvar] = url
            url = ''

        return url


@register.tag
def url_check(parser, token):
    '''
    Template tag that functions like the built-in `url` tag, but renders the URL only if the user
    has permission to access the linked page.

    This can be used to reduce bugs where the permissions tested when accessing the view don't
    match the permissions tested to render the link.

    Should almost always be used with the `as var` syntax e.g.

    {% url_check 'view-name' as href %}
    {% if href %}
      <a href="{{ href }}">Link</a>
    {% endif %}

    This currently only works with class-based views that utilise one (or more) of the
    django.contrib.auth.mixins - for function-based views or any other views, will be identical to
    `url` tag.
    '''
    url_node = defaulttags.url(parser, token)
    return UrlCheckNode(url_node)
