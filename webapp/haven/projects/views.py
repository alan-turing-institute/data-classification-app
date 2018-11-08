from braces.views import UserFormKwargsMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, FormMixin

from identity.mixins import UserRoleRequiredMixin
from identity.roles import ProjectRole, UserRole

from .forms import ProjectAddUserForm, ProjectForm
from .models import Participant, Project


class ProjectCreate(LoginRequiredMixin, UserRoleRequiredMixin, UserFormKwargsMixin, CreateView):
    form_class = ProjectForm
    model = Project

    user_roles = [UserRole.SYSTEM_CONTROLLER, UserRole.RESEARCH_COORDINATOR]

    def get_success_url(self):
        return reverse('projects:list')


class ProjectList(LoginRequiredMixin, ListView):
    model = Project
    context_object_name = 'projects'

    def get_queryset(self):
        participants = Participant.objects.filter(
            user=self.request.user, project=OuterRef('pk')
        )
        return super().get_queryset().get_visible_projects(self.request.user).annotate(
            your_role=Subquery(participants.values('role')[:1])
        )


class ProjectDetail(LoginRequiredMixin, DetailView):
    model = Project

    def get_queryset(self):
        return super().get_queryset().get_visible_projects(self.request.user)

    def get_context_data(self, **kwargs):
        kwargs['participant'] = self.request.user.get_participant(self.get_object())
        return super().get_context_data(**kwargs)


class ProjectAddUser(
    LoginRequiredMixin, UserPassesTestMixin,
    UserFormKwargsMixin, FormMixin, DetailView
):
    model = Project
    template_name = 'projects/project_add_user.html'
    form_class = ProjectAddUserForm

    def get_form(self):
        form = super().get_form()

        creatable_roles = self.request.user.project_role(self.get_object()).creatable_roles

        form.project = self.get_object()
        form.fields['role'].choices = [
            (role, name)
            for (role, name) in form.fields['role'].choices
            if ProjectRole(role) in creatable_roles or role == ''
        ]
        return form

    def get_success_url(self):
        obj = self.get_object()
        if self.request.user.project_role(obj).can_list_participants:
            return reverse('projects:list_participants', args=[obj.id])
        else:
            return reverse('projects:detail', args=[obj.id])

    def get_queryset(self):
        return super().get_queryset().get_visible_projects(self.request.user)

    def test_func(self):
        return self.request.user.project_role(self.get_object()).can_add_participant

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        self.object = self.get_object()
        if form.is_valid():
            form.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class ProjectListParticipants(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Participant
    context_object_name = 'participants'

    def get_project(self):
        if not hasattr(self, '_project'):
            self._project = get_object_or_404(
                Project.objects.get_visible_projects(self.request.user),
                pk=self.kwargs['pk']
            )
        return self._project

    def get_queryset(self):
        return self.get_project().participant_set.all()

    def test_func(self):
        return self.request.user.project_role(self.get_project()).can_list_participants

    def get_context_data(self, **kwargs):
        kwargs.update({
            'project': self.get_project()
        })
        return super().get_context_data(**kwargs)
