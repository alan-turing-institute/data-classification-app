from braces.views import UserFormKwargsMixin
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView

from core.forms import InlineFormSetHelper
from projects.forms import ProjectsForUserInlineFormSet

from .forms import CreateUserForm
from .mixins import UserRoleRequiredMixin
from .models import User
from .roles import UserRole


class UserCreate(LoginRequiredMixin,
                 UserFormKwargsMixin,
                 UserRoleRequiredMixin,
                 CreateView):
    form_class = CreateUserForm
    model = User
    success_url = '/'

    user_roles = [UserRole.SYSTEM_CONTROLLER]

    def get_context_data(self, **kwargs):
        kwargs['helper'] = InlineFormSetHelper()
        kwargs['formset'] = self.get_formset()
        kwargs['editing'] = False
        return super().get_context_data(**kwargs)

    def get_formset(self, **kwargs):
        form_kwargs = {'user': self.request.user}
        if self.request.method == 'POST':
            return ProjectsForUserInlineFormSet(self.request.POST, form_kwargs=form_kwargs)
        else:
            return ProjectsForUserInlineFormSet(form_kwargs=form_kwargs)

    def post(self, request, *args, **kwargs):
        formset = self.get_formset()
        form = self.get_form()
        self.object = None
        if form.is_valid() and formset.is_valid():
            response = self.form_valid(form)
            formset.instance = self.object
            formset.save()
            return response
        else:
            return self.form_invalid(form)


class UserEdit(LoginRequiredMixin,
               UserRoleRequiredMixin,
               DetailView):
    model = User
    template_name = 'identity/user_form.html'

    user_roles = [UserRole.SYSTEM_CONTROLLER]

    def get_success_url(self):
        return reverse('identity:edit_user', args=[self.get_object().id])

    def get_context_data(self, **kwargs):
        kwargs['helper'] = InlineFormSetHelper()
        if 'formset' not in kwargs:
            kwargs['formset'] = self.get_formset()
        kwargs['subject_user'] = self.get_object()
        kwargs['editing'] = True
        return super().get_context_data(**kwargs)

    def get_formset(self, **kwargs):
        form_kwargs = {'user': self.request.user}
        if self.request.method == 'POST':
            return ProjectsForUserInlineFormSet(
                self.request.POST,
                instance=self.get_object(),
                form_kwargs=form_kwargs
            )
        else:
            return ProjectsForUserInlineFormSet(
                instance=self.get_object(),
                form_kwargs=form_kwargs
            )

    def post(self, request, *args, **kwargs):
        formset = self.get_formset()
        self.object = self.get_object()
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(formset=formset))


class UserList(LoginRequiredMixin, ListView):
    """List of users"""

    context_object_name = 'users'
    model = User

    def get_queryset(self):
        return User.objects.get_visible_users(self.request.user)


def import_users(request):

    if "GET" == request.method:
        return HttpResponseRedirect(reverse("identity:list"))

    messages.warning(request, 'User file import has not yet been implemented.')
    return HttpResponseRedirect(reverse("identity:list"))
