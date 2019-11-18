import logging
import re
from collections import defaultdict

from braces.views import UserFormKwargsMixin
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import F, FilteredRelation, Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, FormMixin, UpdateView

from data.forms import SingleQuestionForm
from data.models import ClassificationGuidance, ClassificationQuestion
from identity.mixins import UserPermissionRequiredMixin
from identity.models import User
from identity.roles import UserRole

from .forms import (
    DatasetForWorkPackageInlineFormSet,
    ParticipantForm,
    ParticipantInlineFormSetHelper,
    ParticipantsForWorkPackageApprovalInlineFormSet,
    ParticipantsForWorkPackageInlineFormSet,
    ProjectAddDatasetForm,
    ProjectAddUserForm,
    ProjectAddWorkPackageForm,
    ProjectArchiveForm,
    ProjectForm,
    SaveCancelFormHelper,
    SaveCancelInlineFormSetHelper,
    UsersForProjectInlineFormSet,
    WorkPackageAddDatasetForm,
    WorkPackageAddParticipantForm,
    WorkPackageClassifyDeleteForm,
    WorkPackagesForDatasetInlineFormSet,
    WorkPackagesForParticipantInlineFormSet,
)
from .models import (
    ClassificationOpinion,
    Participant,
    Project,
    ProjectDataset,
    WorkPackage,
    WorkPackageParticipant,
)
from .roles import ProjectRole
from .tables import (
    ClassificationOpinionQuestionTable,
    HistoryTable,
    ParticipantTable,
    PolicyTable,
    ProjectDatasetTable,
    WorkPackageDatasetTable,
    WorkPackageParticipantTable,
    WorkPackageTable,
    bleach_no_links,
)


class ProjectMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._project = None

    def get_project_queryset(self, qs=None):
        if not qs:
            qs = Project.objects
        return qs.get_visible_projects(self.request.user)

    def get_project(self):
        if self._project is None:
            try:
                projects = self.get_project_queryset()
                self._project = projects.get(pk=self.kwargs[self.get_project_url_kwarg()])
            except Project.DoesNotExist:
                raise Http404("No project found matching the query")

        return self._project

    def get_project_url_kwarg(self):
        return 'pk'

    def get_project_role(self):
        """Return the logged in user's administrative role on the project"""
        return self.request.user.project_role(self.get_project())

    def get_project_participation_role(self):
        """Return the logged in user's assigned role on the project"""
        return self.request.user.project_participation_role(self.get_project())

    def get_context_data(self, **kwargs):
        kwargs['project'] = self.get_project()
        kwargs['project_role'] = self.get_project_role()
        return super().get_context_data(**kwargs)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.project = self.get_project()
        return form


class SingleProjectMixin(ProjectMixin, SingleObjectMixin):
    model = Project

    def get_queryset(self):
        return self.get_project_queryset(super().get_queryset())

    def get_project(self):
        return self.get_object()


class WorkPackageMixin(ProjectMixin):
    def get_work_package_queryset(self, qs=None):
        if not qs:
            qs = self.get_project().work_packages
        return qs

    def get_work_package(self):
        try:
            work_packages = self.get_work_package_queryset()
            return work_packages.get(pk=self.kwargs[self.get_work_package_url_kwarg()])
        except WorkPackage.DoesNotExist:
            raise Http404("No work package found matching the query")

    def get_work_package_url_kwarg(self):
        return 'pk'

    def get_project_url_kwarg(self):
        return 'project_pk'

    def get_context_data(self, **kwargs):
        kwargs['work_package'] = self.get_work_package()
        return super().get_context_data(**kwargs)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.work_package = self.get_work_package()
        return form


class SingleWorkPackageMixin(WorkPackageMixin, SingleObjectMixin):
    model = WorkPackage

    def get_queryset(self):
        return self.get_work_package_queryset()

    def get_work_package(self):
        return self.get_object()


class ProjectCreate(
    LoginRequiredMixin, UserPermissionRequiredMixin,
    UserFormKwargsMixin, CreateView
):
    model = Project
    form_class = ProjectForm
    user_permissions = ['can_create_projects']

    def get_success_url(self):
        return reverse('projects:list')

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)
        return super().post(request, *args, **kwargs)


class ProjectList(LoginRequiredMixin, ListView):
    context_object_name = 'projects'
    model = Project

    def get_queryset(self):
        # Store the user's project role on each participant
        return (
            super().get_queryset()
                   .get_visible_projects(self.request.user)
                   .annotate(you=FilteredRelation(
                       'participants', condition=Q(participants__user=self.request.user)))
                   .annotate(your_role=F('you__role'))
                   .annotate(add_time=F('you__created_at'))
                   .order_by(F('add_time').desc(nulls_last=True), '-created_at')
        )


class ProjectDetail(LoginRequiredMixin, SingleProjectMixin, DetailView):
    def get_context_data(self, **kwargs):
        project = self.get_object()
        kwargs['participant'] = self.request.user.get_participant(project)
        participants = project.participants.all()
        kwargs['participants_table'] = ParticipantTable(
            participants, show_edit_links=self.get_project_role().can_edit_participants)
        work_packages = project.work_packages.order_by('created_at').all()
        kwargs['work_packages_table'] = WorkPackageTable(work_packages)
        datasets = project.project_datasets.order_by('created_at').all()
        kwargs['datasets_table'] = ProjectDatasetTable(datasets)
        return SingleProjectMixin.get_context_data(self, **kwargs)


class ProjectEdit(
    LoginRequiredMixin, UserPassesTestMixin,
    SingleProjectMixin, UserFormKwargsMixin, UpdateView
):
    model = Project
    form_class = ProjectForm

    def test_func(self):
        return self.get_project_role().can_edit

    def get_success_url(self):
        obj = self.get_object()
        return reverse('projects:detail', args=[obj.id])

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)
        return super().post(request, *args, **kwargs)


class ProjectArchive(
    LoginRequiredMixin, UserPassesTestMixin,
    FormMixin, SingleProjectMixin, DetailView
):
    template_name = 'projects/project_archive.html'
    form_class = ProjectArchiveForm

    def test_func(self):
        return self.get_project_role().can_archive

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)
        form = self.get_form()
        if form.is_valid():
            self.get_project().archive()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('projects:list')


class ProjectHistory(
    LoginRequiredMixin, UserPassesTestMixin, SingleProjectMixin, DetailView
):
    template_name = 'projects/project_history.html'

    def test_func(self):
        return self.get_project_role().can_view_history

    def get_context_data(self, **kwargs):
        history = self.get_object().get_audit_history()
        kwargs['history_table'] = HistoryTable(history)
        return super().get_context_data(**kwargs)


class ProjectAddUser(
    LoginRequiredMixin, UserPassesTestMixin,
    UserFormKwargsMixin, ProjectMixin, CreateView
):
    model = Participant
    template_name = 'projects/project_add_user.html'
    form_class = ProjectAddUserForm

    def get_context_data(self, **kwargs):
        kwargs['editing'] = False
        kwargs['formset'] = self.get_formset()
        return super().get_context_data(**kwargs)

    def get_form_kwargs(self):
        kwargs = super(ProjectAddUser, self).get_form_kwargs()
        kwargs['project_id'] = self.kwargs['pk']
        return kwargs

    def get_form(self):
        form = super().get_form()

        project_role = self.get_project_role()

        # Restrict form dropdown to roles this user is allowed to assign on the project
        form.fields['role'].choices = [
            (role, name)
            for (role, name) in form.fields['role'].choices
            if project_role.can_assign_role(ProjectRole(role))
        ]
        if not self.get_project().work_packages.exists():
            form.helper = SaveCancelFormHelper('Add Participant')
        else:
            form.helper = FormHelper()
        form.helper.form_tag = False
        return form

    def get_formset(self, **kwargs):
        if not self.get_project().work_packages.exists():
            return None
        options = {
            'form_kwargs': {
                'project': self.get_project(),
                'user': self.request.user,
            },
            'prefix': 'work_packages',
        }

        if self.request.method == 'POST':
            options['data'] = self.request.POST
        formset = WorkPackagesForParticipantInlineFormSet(**options)
        formset.helper = SaveCancelInlineFormSetHelper('Add Participant')
        return formset

    def get_success_url(self):
        obj = self.get_project()
        return reverse('projects:detail', args=[obj.id])

    def test_func(self):
        return self.get_project_role().can_add_participants

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)
        form = self.get_form()
        formset = self.get_formset()
        self.object = None
        if not form.is_valid():
            return self.form_invalid(form)
        elif formset and not formset.is_valid():
            return self.form_invalid(form)
        else:
            response = self.form_valid(form)
            participant = self.object
            if formset:
                formset.instance = participant
                formset.save()
            return response


class EditProjectListParticipants(
    LoginRequiredMixin, UserPassesTestMixin, SingleProjectMixin, DetailView
):
    def __init__(self, *args, **kwargs):
        super(EditProjectListParticipants, self).__init__(*args, **kwargs)

    template_name = 'projects/edit_participant_list.html'

    def get_success_url(self):
        return reverse('projects:detail', args=[self.get_object().id])

    def test_func(self):
        return (self.get_project_role().can_edit_participants
                and self.request.user.user_role.can_view_all_users)

    def get_assignable_roles(self):
        project_role = self.request.user.project_role(self.get_object())
        return [r.value for r in project_role.assignable_roles]

    def get_participants(self):
        roles = self.get_assignable_roles()
        return self.get_object().ordered_participants().filter(role__in=roles)

    def get_context_data(self, **kwargs):
        helper = ParticipantInlineFormSetHelper()
        helper.form_method = 'POST'
        kwargs['helper'] = helper

        kwargs['participants'] = self.get_participants()
        kwargs['project'] = self.get_object()
        if 'formset' not in kwargs:
            kwargs['formset'] = self.get_formset()
        return super().get_context_data(**kwargs)

    def get_formset(self, **kwargs):
        options = {
            'form_kwargs': {
                'user': self.request.user,
                'assignable_roles': self.get_assignable_roles(),
            },
            'instance': self.get_object(),
            'queryset': self.get_participants(),
        }
        if self.request.method == 'POST':
            options['data'] = self.request.POST
        return UsersForProjectInlineFormSet(**options)

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)

        formset = self.get_formset()
        self.object = self.get_object()
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(formset=formset))


class EditParticipant(
    LoginRequiredMixin, UserPassesTestMixin, ProjectMixin, UpdateView
):
    model = Participant
    template_name = 'projects/edit_participant.html'
    form_class = ParticipantForm

    def get_project_url_kwarg(self):
        return 'project_pk'

    def get_context_data(self, **kwargs):
        kwargs['formset'] = self.get_formset()
        kwargs['editing'] = True
        return super().get_context_data(**kwargs)

    def get_form(self):
        form = super().get_form()

        project_role = self.get_project_role()

        # Restrict form dropdown to roles this user is allowed to assign on the project
        form.fields['role'].choices = [
            (role, name)
            for (role, name) in form.fields['role'].choices
            if project_role.can_assign_role(ProjectRole(role))
        ]
        if not self.get_project().work_packages.exists():
            form.helper = SaveCancelFormHelper('Edit Participant')
        else:
            form.helper = FormHelper()
        form.helper.form_tag = False
        return form

    def get_formset(self, **kwargs):
        if not self.get_project().work_packages.exists():
            return None
        options = {
            'form_kwargs': {
                'project': self.get_project(),
                'user': self.request.user,
            },
            'instance': self.get_object(),
            'prefix': 'work_packages',
        }
        if not self.get_project().work_packages.exists():
            options['extra'] = 0
        if self.request.method == 'POST':
            options['data'] = self.request.POST
        formset = WorkPackagesForParticipantInlineFormSet(**options)
        formset.helper = SaveCancelInlineFormSetHelper('Edit Participant')
        return formset

    def get_success_url(self):
        obj = self.get_project()
        return reverse('projects:detail', args=[obj.id])

    def test_func(self):
        return self.get_project_role().can_edit_participants

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)
        self.object = self.get_object()
        form = self.get_form()
        formset = self.get_formset()
        if not form.is_valid():
            return self.form_invalid(form)
        elif formset and not formset.is_valid():
            return self.form_invalid(form)
        else:
            response = self.form_valid(form)
            participant = self.object
            if formset:
                formset.instance = participant
                formset.save()
            return response


class ProjectCreateDataset(
    LoginRequiredMixin, UserPassesTestMixin, UserFormKwargsMixin,
    FormMixin, SingleProjectMixin, DetailView
):
    template_name = 'projects/project_add_dataset.html'
    form_class = ProjectAddDatasetForm

    def get_context_data(self, **kwargs):
        kwargs['editing'] = False
        kwargs['formset'] = self.get_formset()
        return super().get_context_data(**kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project_id'] = self.get_object().id
        return kwargs

    def get_form(self):
        form = super().get_form()

        if not self.get_project().work_packages.exists():
            form.helper = SaveCancelFormHelper('Create Dataset')
        else:
            form.helper = FormHelper()
        form.helper.form_tag = False
        return form

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)

        form = self.get_form()
        formset = self.get_formset()
        self.object = self.get_object()
        if not form.is_valid():
            return self.form_invalid(form)
        elif formset and not formset.is_valid():
            return self.form_invalid(form)
        else:
            dataset = form.save()
            self.object.add_dataset(dataset, dataset.default_representative, request.user)
            if formset:
                formset.instance = dataset
                formset.save()
            return self.form_valid(form)

    def test_func(self):
        return self.get_project_role().can_add_datasets

    def get_success_url(self):
        return reverse('projects:detail', args=[self.get_object().id])

    def get_formset(self, **kwargs):
        if not self.get_project().work_packages.exists():
            return None
        options = {
            'form_kwargs': {
                'project': self.get_project(),
                'user': self.request.user,
            },
            'prefix': 'work_packages',
        }

        if self.request.method == 'POST':
            options['data'] = self.request.POST
        formset = WorkPackagesForDatasetInlineFormSet(**options)
        formset.helper = SaveCancelInlineFormSetHelper('Create Dataset')
        return formset


class ProjectDatasetDetail(LoginRequiredMixin, ProjectMixin, DetailView):
    model = ProjectDataset
    template_name = 'projects/dataset_detail.html'

    def get_queryset(self):
        return ProjectDataset.objects.filter(project=self.get_project())

    def get_project_url_kwarg(self):
        return 'project_pk'

    def get_context_data(self, **kwargs):
        kwargs['dataset'] = self.get_object()
        return super().get_context_data(**kwargs)


class ProjectCreateWorkPackage(
    LoginRequiredMixin, UserPassesTestMixin, UserFormKwargsMixin,
    FormMixin, SingleProjectMixin, DetailView
):
    template_name = 'projects/project_add_work_package.html'
    form_class = ProjectAddWorkPackageForm

    def get_context_data(self, **kwargs):
        kwargs['editing'] = False
        kwargs['formset'] = self.get_formset()
        return super().get_context_data(**kwargs)

    def get_form(self):
        form = super().get_form()

        if not self.get_project().datasets.exists():
            form.helper = SaveCancelFormHelper('Create Work Package')
        else:
            form.helper = FormHelper()
        form.helper.form_tag = False
        return form

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)

        form = self.get_form()
        formset = self.get_formset()
        self.object = self.get_object()
        if not form.is_valid():
            return self.form_invalid(form)
        elif formset and not formset.is_valid():
            return self.form_invalid(form)
        else:
            work_package = form.save(commit=False)
            self.object.add_work_package(work_package, form.user)
            work_package.save()
            form.save_m2m()
            if formset:
                formset.instance = work_package
                formset.save()
            return self.form_valid(form)

    def test_func(self):
        return self.get_project_role().can_add_work_packages

    def get_success_url(self):
        return reverse('projects:detail', args=[self.get_object().id])

    def get_formset(self, **kwargs):
        if not self.get_project().datasets.exists():
            return None
        options = {
            'form_kwargs': {
                'project': self.get_project(),
                'user': self.request.user,
            },
            'prefix': 'datasets',
        }

        if self.request.method == 'POST':
            options['data'] = self.request.POST
        formset = DatasetForWorkPackageInlineFormSet(**options)
        formset.helper = SaveCancelInlineFormSetHelper('Create Work Package')
        return formset


class WorkPackageDetail(LoginRequiredMixin, SingleWorkPackageMixin, DetailView):
    template_name = 'projects/work_package_detail.html'

    def get_context_data(self, **kwargs):
        work_package = self.get_object()
        kwargs['participant'] = self.request.user.get_participant(work_package.project)
        context = SingleWorkPackageMixin.get_context_data(self, **kwargs)

        datasets = work_package.work_package_datasets.all()
        context['datasets_table'] = WorkPackageDatasetTable(datasets)

        participants = work_package.get_participants_with_approval(self.request.user)
        context['participants_table'] = WorkPackageParticipantTable(
            participants, work_package=work_package, user=self.request.user)

        context['can_classify'] = work_package.has_datasets and not work_package.has_tier
        context['has_classified'] = work_package.has_user_classified(self.request.user)

        if work_package.has_tier:
            # Don't show these until we have a tier, to avoid influencing anybody that
            # hasn't classified yet
            policies = work_package.get_policies()
            context['policy_table'] = PolicyTable(policies)

            classifications = work_package.classifications.all()
            context['question_table'] = ClassificationOpinionQuestionTable(classifications)

        context['show_approve_participants'] = work_package.show_approve_participants(
            self.request.user)
        return context


class WorkPackageAddDataset(
    LoginRequiredMixin, UserPassesTestMixin,
    UserFormKwargsMixin, SingleWorkPackageMixin, FormMixin, DetailView
):
    template_name = 'projects/work_package_add_dataset.html'
    form_class = WorkPackageAddDatasetForm

    def get_success_url(self):
        return self.object.get_absolute_url()

    def test_func(self):
        return self.get_project_role().can_add_work_packages

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.setdefault('work_package', self.get_object())
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if "cancel" in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)
        form = self.get_form()
        if form.is_valid():
            form.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class WorkPackageApproveParticipants(
    LoginRequiredMixin, UserPassesTestMixin, SingleWorkPackageMixin, DetailView
):
    template_name = 'projects/work_package_participant_approve.html'

    def test_func(self):
        return self.get_project_role().can_approve_participants

    def get_context_data(self, **kwargs):
        helper = SaveCancelInlineFormSetHelper('Approve Participants')
        kwargs['helper'] = helper
        kwargs['formset'] = self.get_formset()
        kwargs['editing'] = True
        return super().get_context_data(**kwargs)

    def get_formset(self, **kwargs):
        work_package = self.get_object()
        user = self.request.user
        options = {
            'form_kwargs': {
                'user': user,
            },
            'instance': work_package,
            'prefix': 'participants',
            'queryset': work_package.get_work_package_participants_to_approve(user),
        }
        if self.request.method == 'POST':
            options['data'] = self.request.POST
        return ParticipantsForWorkPackageApprovalInlineFormSet(**options)

    def get_success_url(self):
        obj = self.get_project()
        return reverse('projects:detail', args=[obj.id])

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)
        self.object = self.get_object()
        formset = self.get_formset()
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data())


class WorkPackageEditParticipants(
    LoginRequiredMixin, UserPassesTestMixin, SingleWorkPackageMixin, DetailView
):
    template_name = 'projects/work_package_participants_edit.html'

    def test_func(self):
        return self.get_project_role().can_edit_participants

    def get_context_data(self, **kwargs):
        helper = SaveCancelInlineFormSetHelper()
        kwargs['helper'] = helper
        kwargs['formset'] = self.get_formset()
        kwargs['editing'] = True
        return super().get_context_data(**kwargs)

    def get_formset(self, **kwargs):
        work_package = self.get_object()
        user = self.request.user
        options = {
            'form_kwargs': {
                'user': user,
            },
            'instance': work_package,
            'prefix': 'participants',
            'queryset': work_package.work_package_participants,
        }
        if self.request.method == 'POST':
            options['data'] = self.request.POST
        return ParticipantsForWorkPackageInlineFormSet(**options)

    def get_success_url(self):
        obj = self.get_project()
        return reverse('projects:detail', args=[obj.id])

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)
        self.object = self.get_object()
        formset = self.get_formset()
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data())


class WorkPackageAddParticipant(
    LoginRequiredMixin, UserPassesTestMixin,
    UserFormKwargsMixin, WorkPackageMixin, CreateView
):
    template_name = 'projects/work_package_add_participant.html'
    model = WorkPackageParticipant
    form_class = WorkPackageAddParticipantForm

    def get_success_url(self):
        return self.get_work_package().get_absolute_url()

    def test_func(self):
        return self.get_project_role().can_add_participants

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.setdefault('work_package', self.get_work_package())
        return kwargs

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)
        form = self.get_form()
        if form.is_valid():
            form.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class WorkPackageClassifyData(
    LoginRequiredMixin, UserPassesTestMixin, SingleWorkPackageMixin, TemplateView
):
    template_name = 'projects/work_package_classify_data.html'

    def test_func(self):
        role = self.get_project_role()
        if not role.can_classify_data:
            return False
        participant = self.request.user.get_participant(self.get_project())
        if not participant.get_work_package_participant(self.get_work_package()):
            return False
        return True

    def get(self, *args, **kwargs):
        response = self.check_already_classified()
        if response:
            return response

        response = self.load_questions()
        if response:
            return response

        context = self.get_context_data()
        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        response = self.check_already_classified()
        if response:
            return response

        response = self.load_questions()
        if response:
            return response

        answer = None
        if 'submit_yes' in self.request.POST:
            self.store_answer(self.question, True)
            answer = self.question.answer_yes()
        elif 'submit_no' in self.request.POST:
            self.store_answer(self.question, False)
            answer = self.question.answer_no()

        if answer is not None:
            if isinstance(answer, int):
                return self.save_results(answer)
            else:
                return self.redirect_to_question(answer)

        context = self.get_context_data()
        return self.render_to_response(context)

    def check_already_classified(self):
        """
        Before doing anything on this view, determine whether this user has
        already classified the work package.

        If they have (and they're not trying to modify it), then show their classification (and
        others) rather than display the form again.
        """
        self.object = self.get_object()
        self.start_modification = bool(self.request.GET.get('modify', False))

        if self.start_modification or self.is_modification():
            return None

        classification = ClassificationOpinion.objects.filter(
            work_package=self.object,
            created_by=self.request.user
        ).first()
        if classification:
            message = ('You have already completed classification. Please delete your '
                       'classification and start again if you wish to change any answers.')
            return self.redirect_to_results(message=message, message_level=messages.ERROR)
        return None

    def load_questions(self):
        '''
        Retrieve the current question to be answered, according to the URL

        If there isn't a question identified in the URL, user will be redirected to the starting
        question
        '''
        self.starting_question = ClassificationQuestion.objects.get_starting_question()
        self.previous_question = None
        if 'question_pk' not in self.kwargs:
            if self.start_modification:
                response = self.store_previous_answers(self.starting_question)
                if response:
                    return response
            else:
                self.clear_answers()
            return self.redirect_to_question(self.starting_question)
        else:
            self.question = ClassificationQuestion.objects.get(pk=self.kwargs['question_pk'])
            if self.start_modification:
                response = self.store_previous_answers(self.question)
                if response:
                    return response
            self.clear_answers(after=self.question)
        self.previous_question = self.get_previous_question()
        return None

    def save_results(self, expected_tier):
        '''
        Get all the answers from the session, and save the classification to the database
        '''
        questions = []
        question = self.starting_question
        tier = None
        # Although we try to make sure the session only contains relevant answers, e.g. calling
        # clear_answers if the user has went back and changed answers, it's possible something
        # invalid might be in there. Therefore, we don't just copy the session, we follow the
        # chain from the starting question and only store what matches
        while True:
            answer = self.get_answer(question)
            if answer is None:
                logging.error(f"No response found in session for question {question.name}")
                message = 'An error occurred storing the results of your classification.'
                return self.redirect_to_question(None, message, message_level=messages.ERROR)

            questions.append((question, answer))
            if answer:
                question = question.answer_yes()
            else:
                question = question.answer_no()

            if isinstance(question, int):
                tier = question
                break

        if tier != expected_tier:
            logging.error(f"Unexpected tier storing result: expected {expected_tier}, was {tier}")
            message = 'An error occurred storing the results of your classification.'
            return self.redirect_to_question(None, message, message_level=messages.ERROR)

        if self.is_modification():
            self.object.classification_for(self.request.user).delete()
        self.object.classify_as(tier, self.request.user, questions)
        self.object.calculate_tier()
        self.clear_answers()
        return self.redirect_to_results()

    def format_answer(self, answer):
        if isinstance(answer, int):
            return f"Classify as <strong>Tier {answer}</strong>"
        question = bleach_no_links(answer.question)
        return f'<span class="text-muted">Next Question: {question}</span>'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use a regex to identify links to guidance
        # Some form of HTML parser might be better, but we're looking for a very limited
        # pattern so is hopefully unnecessary
        pattern = re.compile('href="#([^"]+)"')
        matches = [m for m in pattern.finditer(self.question.question)]
        if matches:
            guidance = []
            all_guidance = {g.name: g for g in ClassificationGuidance.objects.all()}
            while matches:
                match = matches.pop(0)
                name = match.group(1)
                g = all_guidance.get(name)
                if g and g not in guidance:
                    guidance.append(g)
                    matches.extend([m for m in pattern.finditer(g.guidance)])

            context['guidance'] = guidance

        context['question'] = self.question
        context['answer_yes'] = self.format_answer(self.question.answer_yes())
        context['answer_no'] = self.format_answer(self.question.answer_no())
        context['starting_question'] = self.starting_question
        context['question_number'] = self.get_question_number()
        if self.previous_question:
            context['previous_question'] = self.previous_question
        return context

    def redirect_to_question(self, question, message=None, message_level=None):
        if message:
            message_level = message_level or messages.INFO
            messages.add_message(self.request, message_level, message)
        args = [self.object.project.id, self.object.id]
        if question:
            args.append(question.id)
        url = reverse('projects:classify_data', args=args)
        return HttpResponseRedirect(url)

    def redirect_to_results(self, message=None, message_level=None):
        if message:
            message_level = message_level or messages.INFO
            messages.add_message(self.request, message_level, message)
        args = [self.object.project.id, self.object.id]
        url = reverse('projects:classify_results', args=args)
        return HttpResponseRedirect(url)

    @property
    def session_key(self):
        return f"classification_{self.object.pk}"

    @property
    def session_modification_key(self):
        return f"classification_modification_{self.object.pk}"

    def store_answer(self, question, answer):
        '''
        Store the answer to the given question in the session
        '''
        existing = self.request.session.get(self.session_key)
        if not existing:
            existing = []
        # Cannot append to existing object in session, will not serialize correctly
        self.request.session[self.session_key] = existing + [[question.name, answer]]

    def get_previous_question(self):
        '''
        Return the ClassificationQuestion representing the last question the user answered
        '''
        answers = self.request.session.get(self.session_key)
        if answers:
            name = answers[-1][0]
            if name:
                return ClassificationQuestion.objects.get(name=name)
        return None

    def is_modification(self):
        '''
        Determine if this is during a modification
        '''
        return self.request.session.get(self.session_modification_key, False)

    def get_answer(self, question):
        '''
        Retrieve the answer for the given question from the session
        '''
        answers = self.request.session.get(self.session_key)
        if answers:
            for answer in answers:
                if answer[0] == question.name:
                    return answer[1]
        return None

    def get_question_number(self):
        answers = self.request.session.get(self.session_key)
        number = 1
        if answers:
            number += len(answers)
        return number

    def clear_answers(self, after=None):
        '''
        Remove answers from the session

        If `after` is None (the default), all answers will be removed.

        Otherwise `after` should be a ClassificationQuestion instance. Answers for any
        questions before (but not including) that question will remain in the session, but
        anything else is removed.
        '''
        if not after:
            self.request.session.pop(self.session_key, None)
            self.request.session.pop(self.session_modification_key, None)
            return

        answers = self.request.session.get(self.session_key)
        if answers:
            upto = None
            for i, answer in enumerate(answers):
                if answer[0] == after.name:
                    upto = i
                    break

            if upto is not None:
                self.request.session[self.session_key] = answers[:upto]

    def store_previous_answers(self, upto):
        '''
        Retrieve the user's previous classification from the database, and store it in the session

        upto is the question to start the modification process from

        If something goes wrong (either because the user is trying to modify a question they never
        answered in the first place, or because a question has been changed in the meantime), then
        the user may be redirected to modify an earlier question than the one they actually chose
        to.
        '''
        self.request.session[self.session_key] = []
        self.request.session[self.session_modification_key] = True

        classification = self.object.classification_for(self.request.user).first()
        answered_questions = {}
        if classification:
            for q in classification.questions.all():
                key = (q.question.id, q.question_version)
                answered_questions[key] = q.answer

        q = self.starting_question
        while q and not isinstance(q, int) and q != upto:
            try:
                key = (q.id, q.history.latest().history_id)
                answer = answered_questions[key]
                self.store_answer(q, answer)
                if answer:
                    q = q.answer_yes()
                else:
                    q = q.answer_no()
            except KeyError:
                message = ('Some recorded answers could not be retrieved. Please begin the '
                           'classification process from the question below.')
                return self.redirect_to_question(q, message)
        if q != upto:
            message = ('Recorded answers could not be retrieved. Please begin the classification '
                       'process from the question below.')
            return self.redirect_to_question(self.starting_question, message)


class WorkPackageClassifyResults(
    LoginRequiredMixin, UserPassesTestMixin, SingleWorkPackageMixin, DetailView
):
    template_name = 'projects/work_package_classify_results.html'

    def get(self, *args, **kwargs):
        self.object = self.get_object()

        role = self.get_project_role()
        classification = None
        other_classifications = []
        if role.can_classify_data:
            classification = self.object.classification_for(self.request.user).first()
            if classification:
                # Only show other classifications once the user has completed classification
                other_classifications = self.object.classifications.exclude(
                    created_by=self.request.user)
        else:
            other_classifications = self.object.classifications.all()

        context = {
            'work_package': self.object,
            'classification': classification,
            'other_classifications': other_classifications,
        }
        if not self.object.has_tier:
            all_classifications = list(other_classifications)
            current_user = None
            if classification:
                all_classifications.insert(0, classification)
                current_user = self.request.user
            if all_classifications:
                context['questions_table'] = ClassificationOpinionQuestionTable(
                    all_classifications, current_user=current_user)

        return render(self.request, 'projects/work_package_classify_results.html', context)

    def test_func(self):
        role = self.get_project_role()
        return role.can_view_classification if role else False


class WorkPackageClassifyDelete(
    LoginRequiredMixin, UserPassesTestMixin,
    FormMixin, SingleWorkPackageMixin, DetailView
):
    template_name = 'projects/work_package_classify_delete.html'
    form_class = WorkPackageClassifyDeleteForm

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)
        form = self.get_form()
        if form.is_valid():
            self.object.classification_for(self.request.user).delete()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def test_func(self):
        role = self.get_project_role()
        if not role or not role.can_classify_data:
            return False
        self.object = self.get_object()
        if self.object.has_tier:
            return False
        return self.object.classification_for(self.request.user).exists()

    def get_success_url(self):
        return self.object.get_absolute_url()


class GroupedSelect2QuerySetView(autocomplete.Select2QuerySetView):
    '''
    Extends Select2QuerySetView to allow grouping of results (in a similar way to
    Select2GroupListView)

    Subclasses should define a get_result_group method which receives the same result
    object as get_result_value etc., and return a 2-tuple of (group_id, group_label).
    The resulting groups will be sorted by group_id.
    '''

    def get_results(self, context):
        grouped = defaultdict(list)
        for result in context['object_list']:
            group = self.get_result_group(result)
            if int(self.request.GET.get('page', '1')) > 1:
                group = (group[0], group[1] + '...')
            grouped[group].append(result)

        results = []
        keys = sorted(grouped.keys())
        for key in keys:
            group = grouped[key]
            if group:
                results.append({
                    'id': key[0],
                    'text': key[1],
                    'children': super().get_results({'object_list': group})
                })
        return results


class AutocompleteNewParticipant(autocomplete.Select2QuerySetView):
    """
    Autocomplete username from list of Users who are not currently participants in this project
    """

    def get_queryset(self):

        qs = self.get_visible_users()
        if self.q:
            for term in self.q.split():
                qs = qs.filter(
                    Q(first_name__icontains=term) |
                    Q(last_name__icontains=term) |
                    Q(username__icontains=term)
                )

        return qs

    def get_visible_users(self):
        # Filter results depending on user role permissions
        if not self.request.user.user_role.can_view_all_users:
            return User.objects.none()

        existing_users = self.get_users_to_exclude()
        if existing_users is not None:
            return User.objects.exclude(pk__in=existing_users)

        return User.objects.all()

    def get_users_to_exclude(self):
        if 'pk' in self.kwargs:
            # Autocomplete suggestions are users not already participating in this project
            project_id = self.kwargs['pk']
            return Project.objects.get(pk=project_id).participants.values('user')
        return None

    def get_result_label(self, user):
        return user.display_name()


class AutocompleteDataProviderRepresentative(AutocompleteNewParticipant,
                                             GroupedSelect2QuerySetView):
    """
    Autocomplete username from list of Users who are not currently participants in this project,
    or are DPRs
    """

    def get_visible_users(self):
        if not self.request.user.user_role.can_view_all_users:
            if 'pk' in self.kwargs:
                project_id = self.kwargs['pk']
                return User.objects.filter(
                    participants__project__pk=project_id,
                    participants__role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value
                )
        return super().get_visible_users()

    def get_users_to_exclude(self):
        if 'pk' in self.kwargs:
            project_id = self.kwargs['pk']
            participants = Project.objects.get(pk=project_id).participants
            participants = participants.exclude(role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value)
            return participants.values('user')

        return None

    def get_queryset(self):
        qs = super().get_queryset()
        if 'pk' in self.kwargs:
            project_id = self.kwargs['pk']
            qs = qs.annotate(you=FilteredRelation(
                'participants',
                condition=Q(participants__project=project_id))
            )
            qs = qs.annotate(project_role=F('you__role'))
        return qs

    def get_result_group(self, result):
        if result.project_role == ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value:
            return (0, 'Data Provider Representatives')
        return (1, 'Other users')
