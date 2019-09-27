import logging
import re
from collections import OrderedDict

from braces.views import UserFormKwargsMixin
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

from core.forms import InlineFormSetHelper
from data.forms import SingleQuestionForm
from data.models import ClassificationGuidance, ClassificationQuestion
from identity.mixins import UserPermissionRequiredMixin
from identity.models import User
from identity.roles import UserRole

from .forms import (
    ParticipantForm,
    ParticipantInlineFormSetHelper,
    ParticipantsForWorkPackageInlineFormSet,
    ProjectAddDatasetForm,
    ProjectAddUserForm,
    ProjectAddWorkPackageForm,
    ProjectForm,
    UsersForProjectInlineFormSet,
    WorkPackageAddDatasetForm,
    WorkPackageAddParticipantForm,
    WorkPackageClassifyDeleteForm,
    WorkPackagesForParticipantInlineFormSet,
)
from .models import (
    ClassificationOpinion,
    Participant,
    Project,
    WorkPackage,
    WorkPackageParticipant,
)
from .roles import ProjectRole
from .tables import (
    ClassificationOpinionQuestionTable,
    DatasetTable,
    HistoryTable,
    ParticipantTable,
    PolicyTable,
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
        return super().get_queryset().\
            get_visible_projects(self.request.user).\
            annotate(you=FilteredRelation(
                'participants',
                condition=Q(participants__user=self.request.user))
            ).\
            annotate(your_role=F('you__role')).\
            annotate(add_time=F('you__created_at')).\
            order_by(F('add_time').desc(nulls_last=True), '-created_at')


class ProjectDetail(LoginRequiredMixin, SingleProjectMixin, DetailView):
    def get_context_data(self, **kwargs):
        project = self.get_object()
        kwargs['participant'] = self.request.user.get_participant(project)
        participants = project.participants.all()
        kwargs['participants_table'] = ParticipantTable(participants)
        work_packages = project.work_packages.all()
        kwargs['work_packages_table'] = WorkPackageTable(work_packages)
        datasets = project.datasets.all()
        kwargs['datasets_table'] = DatasetTable(datasets)
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
        helper = InlineFormSetHelper()
        helper.add_input(Submit('submit', 'Add Participant'))
        helper.add_input(Submit('cancel', 'Cancel',
                                css_class='btn-secondary',
                                formnovalidate='formnovalidate'))

        kwargs['helper'] = helper
        kwargs['formset'] = self.get_formset()
        kwargs['editing'] = False
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
        return form

    def get_formset(self, **kwargs):
        options = {
            'form_kwargs': {
                'project': self.get_project(),
                'user': self.request.user,
            },
            'prefix': 'work_packages',
        }

        if self.request.method == 'POST':
            options['data'] = self.request.POST
        return WorkPackagesForParticipantInlineFormSet(**options)

    def get_success_url(self):
        obj = self.get_project()
        if self.get_project_role().can_list_participants:
            return reverse('projects:list_participants', args=[obj.id])
        else:
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
        if form.is_valid() and formset.is_valid():
            response = self.form_valid(form)
            participant = self.object
            formset.instance = participant
            formset.save()
            return response
        else:
            return self.form_invalid(form)


class ProjectListParticipants(
    LoginRequiredMixin, UserPassesTestMixin, SingleProjectMixin, DetailView
):
    template_name = 'projects/participant_list.html'

    def test_func(self):
        return self.get_project_role().can_list_participants

    def get_context_data(self, **kwargs):
        kwargs['ordered_participants'] = self.get_object().ordered_participants()
        kwargs.update({"accessing_user": self.request.user})
        return super().get_context_data(**kwargs)


class EditProjectListParticipants(
    LoginRequiredMixin, UserPassesTestMixin, SingleProjectMixin, DetailView
):
    def __init__(self, *args, **kwargs):
        super(EditProjectListParticipants, self).__init__(*args, **kwargs)

    template_name = 'projects/edit_participant_list.html'

    def get_success_url(self):
        return reverse('projects:list_participants', args=[self.get_object().id])

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
        # Use crispy FormHelper to add submit and cancel buttons
        helper.add_input(Submit('submit', 'Save Changes'))
        helper.add_input(Submit('cancel', 'Cancel',
                                css_class='btn-secondary',
                                formnovalidate='formnovalidate'))
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
        helper = InlineFormSetHelper()
        helper.add_input(Submit('submit', 'Edit Participant'))
        helper.add_input(Submit('cancel', 'Cancel',
                                css_class='btn-secondary',
                                formnovalidate='formnovalidate'))

        kwargs['helper'] = helper
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
        return form

    def get_formset(self, **kwargs):
        options = {
            'form_kwargs': {
                'project': self.get_project(),
                'user': self.request.user,
            },
            'instance': self.get_object(),
            'prefix': 'work_packages',
        }
        if self.request.method == 'POST':
            options['data'] = self.request.POST
        return WorkPackagesForParticipantInlineFormSet(**options)

    def get_success_url(self):
        obj = self.get_project()
        if self.get_project_role().can_list_participants:
            return reverse('projects:list_participants', args=[obj.id])
        else:
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
        if form.is_valid() and formset.is_valid():
            response = self.form_valid(form)
            participant = self.object
            formset.instance = participant
            formset.save()
            return response
        else:
            return self.form_invalid(form)


class ProjectListDatasets(
    LoginRequiredMixin, SingleProjectMixin, DetailView
):
    template_name = 'projects/dataset_list.html'

    def get_context_data(self, **kwargs):
        kwargs['datasets'] = self.get_object().datasets.all()
        return super().get_context_data(**kwargs)


class ProjectCreateDataset(
    LoginRequiredMixin, UserPassesTestMixin, UserFormKwargsMixin,
    FormMixin, SingleProjectMixin, DetailView
):
    template_name = 'projects/project_add_dataset.html'
    form_class = ProjectAddDatasetForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        participants = self.get_object().participants
        participants = participants.filter(role=ProjectRole.DATA_PROVIDER_REPRESENTATIVE.value)
        users = User.objects.filter(id__in=participants.values_list('user', flat=True))
        kwargs['representative_qs'] = users
        return kwargs

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)

        form = self.get_form()
        self.object = self.get_object()
        if form.is_valid():
            dataset = form.save()
            self.object.add_dataset(dataset, dataset.default_representative, request.user)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def test_func(self):
        return self.get_project_role().can_add_datasets

    def get_success_url(self):
        return reverse('projects:detail', args=[self.get_object().id])


class ProjectListWorkPackages(
    LoginRequiredMixin, SingleProjectMixin, DetailView
):
    template_name = 'projects/work_package_list.html'

    def get_context_data(self, **kwargs):
        kwargs['work_packages'] = self.get_object().work_packages.order_by('created_at').all()
        return super().get_context_data(**kwargs)


class ProjectCreateWorkPackage(
    LoginRequiredMixin, UserPassesTestMixin, UserFormKwargsMixin,
    FormMixin, SingleProjectMixin, DetailView
):
    template_name = 'projects/project_add_work_package.html'
    form_class = ProjectAddWorkPackageForm

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)

        form = self.get_form()
        self.object = self.get_object()
        if form.is_valid():
            work_package = form.save(commit=False)
            work_package.created_by = form.user
            work_package.project = self.object
            work_package.save()
            form.save_m2m()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def test_func(self):
        return self.get_project_role().can_add_work_packages

    def get_success_url(self):
        return reverse('projects:detail', args=[self.get_object().id])


class WorkPackageDetail(LoginRequiredMixin, SingleWorkPackageMixin, DetailView):
    template_name = 'projects/work_package_detail.html'

    def get_context_data(self, **kwargs):
        work_package = self.get_object()
        kwargs['participant'] = self.request.user.get_participant(work_package.project)
        context = SingleWorkPackageMixin.get_context_data(self, **kwargs)

        datasets = work_package.datasets.all()
        context['datasets_table'] = DatasetTable(datasets)

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


class WorkPackageListDatasets(
    LoginRequiredMixin, SingleWorkPackageMixin, DetailView
):
    template_name = 'projects/work_package_dataset_list.html'

    def get_context_data(self, **kwargs):
        kwargs['datasets'] = self.get_object().datasets.all()
        return super().get_context_data(**kwargs)


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
        if "cancel" in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)
        form = self.get_form()
        self.object = self.get_object()
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
        helper = InlineFormSetHelper()
        helper.add_input(Submit('submit', 'Approve Participants'))
        helper.add_input(Submit('cancel', 'Cancel',
                                css_class='btn-secondary',
                                formnovalidate='formnovalidate'))

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
        return ParticipantsForWorkPackageInlineFormSet(**options)

    def get_success_url(self):
        obj = self.get_project()
        if self.get_project_role().can_list_participants:
            return reverse('projects:list_participants', args=[obj.id])
        else:
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
    session_key = 'classification'

    def test_func(self):
        role = self.get_project_role()
        return role.can_classify_data if role else False

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
        self.modify = bool(self.request.GET.get('modify', False))

        if self.modify:
            return None

        classification = ClassificationOpinion.objects.filter(
            work_package=self.object,
            created_by=self.request.user
        ).first()
        if classification:
            message = ('You have already completed classification. Please delete your '
                       'classification if you wish to change any answers.')
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
            self.clear_answers()
            return self.redirect_to_question(self.starting_question)
        else:
            self.question = ClassificationQuestion.objects.get(pk=self.kwargs['question_pk'])
            if self.modify:
                response = self.store_previous_answers()
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

        if self.modify:
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
        context['modify'] = self.modify
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
        if self.modify:
            url += '?modify=1'
        return HttpResponseRedirect(url)

    def redirect_to_results(self, message=None, message_level=None):
        if message:
            message_level = message_level or messages.INFO
            messages.add_message(self.request, message_level, message)
        args = [self.object.project.id, self.object.id]
        url = reverse('projects:classify_results', args=args)
        return HttpResponseRedirect(url)

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

    def store_previous_answers(self):
        '''
        Retrieve the user's previous classification from the database, and store it in the session

        If something goes wrong (either because the user is trying to modify a question they never
        answered in the first place, or because a question has been changed in the meantime), then
        the user may be redirected to modify an earlier question than the one they actually chose
        to.
        '''
        if self.request.session.get(self.session_key) is not None:
            return
        self.request.session[self.session_key] = []

        classification = self.object.classification_for(self.request.user).first()
        answered_questions = {}
        if classification:
            for q in classification.questions.all():
                key = (q.question.id, q.question_version)
                answered_questions[key] = q.answer

        q = self.starting_question
        while q and not isinstance(q, int) and q != self.question:
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
        if q != self.question:
            message = ('Recorded answers could not be retrieved. Please begin the classification '
                       'process from the question below.')
            return self.redirect_to_question(self.starting_question, message)


class WorkPackageClassifyResults(
    LoginRequiredMixin, UserPassesTestMixin, SingleWorkPackageMixin, DetailView
):
    template_name = 'projects/work_package_classify_results.html'

    def dispatch(self, *args, **kwargs):
        self.object = self.get_object()

        # Before doing anything on this view, determine whether this user has already classified
        # the work package. If they have not, then redirect them to the classification form.
        classification = self.object.classification_for(self.request.user).first()
        if not classification:
            url = reverse('projects:classify_data', args=[self.object.project.id, self.object.id])
            return HttpResponseRedirect(url)

        # Show the classification result, along with that of other users (and the project's final
        # classification, if available yet)

        other_classifications = self.object.classifications.exclude(created_by=self.request.user)

        table = ClassificationOpinionQuestionTable(
            [classification] + list(other_classifications)
        )

        return render(self.request, 'projects/work_package_classify_results.html', {
            'classification': classification,
            'other_classifications': other_classifications,
            'project_tier': self.object.tier,
            'questions_table': table,
        })

    def test_func(self):
        role = self.get_project_role()
        return role.can_classify_data if role else False


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


class NewParticipantAutocomplete(autocomplete.Select2QuerySetView):
    """
    Autocomplete username from list of Users who are not currently participants in this project
    """
    def get_queryset(self):

        # Filter results depending on user role permissions
        if not self.request.user.user_role.can_view_all_users:
            return User.objects.none()

        if 'pk' in self.kwargs:
            # Autocomplete suggestions are users not already participating in this project
            project_id = self.kwargs['pk']
            existing_users = Project.objects.get(pk=project_id).participants.values('user')
            qs = User.objects.exclude(pk__in=existing_users)
        else:
            qs = User.objects.all()

        if self.q:
            for term in self.q.split():
                qs = qs.filter(
                    Q(first_name__icontains=term) |
                    Q(last_name__icontains=term) |
                    Q(username__icontains=term)
                )

        return qs

    def get_result_label(self, user):
        return user.display_name()
