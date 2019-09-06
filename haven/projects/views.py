import re
from collections import OrderedDict

from braces.views import UserFormKwargsMixin
from crispy_forms.layout import Submit
from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import F, FilteredRelation, Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, FormMixin, UpdateView
from formtools.wizard.views import SessionWizardView

from core.forms import InlineFormSetHelper
from data.forms import SingleQuestionForm
from data.models import ClassificationGuidance, ClassificationQuestion
from identity.mixins import UserRoleRequiredMixin
from identity.models import User
from identity.roles import UserRole
from projects.forms import (
    ParticipantInlineFormSetHelper,
    UsersForProjectInlineFormSet,
)

from .forms import (
    ProjectAddDatasetForm,
    ProjectAddUserForm,
    ProjectAddWorkPackageForm,
    ProjectForm,
    WorkPackageAddDatasetForm,
    WorkPackageClassifyDeleteForm,
)
from .models import ClassificationOpinion, Participant, Project, WorkPackage
from .roles import ProjectRole
from .tables import (
    ClassificationOpinionQuestionTable,
    DatasetTable,
    HistoryTable,
    ParticipantTable,
    PolicyTable,
    WorkPackageTable,
)


class ProjectMixin:
    def get_project_queryset(self, qs=None):
        if not qs:
            qs = Project.objects
        return qs.get_visible_projects(self.request.user)

    def get_project(self):
        try:
            projects = self.get_project_queryset()
            return projects.get(id=self.kwargs[self.get_project_url_kwarg()])
        except Project.DoesNotExist:
            raise Http404("No project found matching the query")

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


class SingleWorkPackageMixin(ProjectMixin, SingleObjectMixin):
    model = WorkPackage
    context_object_name = 'work_package'

    def get_project_url_kwarg(self):
        return 'project_pk'

    def get_queryset(self):
        return self.get_project().work_packages

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.work_package = self.get_object()
        return form


class ProjectCreate(
    LoginRequiredMixin, UserRoleRequiredMixin,
    UserFormKwargsMixin, CreateView
):
    model = Project
    form_class = ProjectForm

    user_roles = [UserRole.SYSTEM_MANAGER, UserRole.PROGRAMME_MANAGER]

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
        self.object = None
        if form.is_valid():
            return self.form_valid(form)
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

        if work_package.has_tier:
            # Don't show these until we have a tier, to avoid influencing anybody that
            # hasn't classified yet
            policies = work_package.get_policies()
            context['policy_table'] = PolicyTable(policies)

            classifications = work_package.classifications.all()
            context['question_table'] = ClassificationOpinionQuestionTable(classifications)

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


class WorkPackageClassifyData(
    LoginRequiredMixin, UserPassesTestMixin, SingleWorkPackageMixin, SessionWizardView
):
    template_name = 'projects/work_package_classify_data.html'
    form_list = [
        ('_', SingleQuestionForm)
    ]

    def dispatch(self, *args, **kwargs):
        """
        Before doing anything on this view, determine whether this user has
        already classified the work package.

        If they have, then show their classification (and others) rather than
        display the form again.
        """
        if self.request.user.is_authenticated:
            self.object = self.get_object()

            classification = ClassificationOpinion.objects.filter(
                work_package=self.object,
                created_by=self.request.user
            ).first()
            if classification:
                return self.render_result(classification)

        self.form_list = OrderedDict()
        self.condition_dict = {}
        first_step = None
        for q in ClassificationQuestion.objects.get_ordered_questions():
            if not first_step:
                first_step = q.name
            # SessionWizardView doesn't support having a form_list that
            # changes from step to step, so instead it needs to contain all
            # the forms, and use the condition_dict to determine which to show
            self.form_list[q.name] = SingleQuestionForm.subclass_for_question(q)
            self.condition_dict[q.name] = self.show_step(q, first_step)

        return super().dispatch(*args, *kwargs)

    def show_step(self, question, first_step):
        def f(wizard):
            # The condition needs to be true not just for the current step, but
            # also all the steps leading up to it. However, you can't just check
            # whether a step already has data, because that interferes with the
            # ability to go backwards, so you need to follow the chain of
            # submitted forms
            chain = []
            next_step = first_step
            while True:
                chain.append(next_step)
                data = self.get_cleaned_data_for_step(next_step)
                if not data:
                    break
                next_step = data.get('next_step')
                if not next_step:
                    break
            return question.name in chain
        return f

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)

        # Use a regex to identify links to guidance
        # Some form of HTML parser might be better, but we're looking for a very limited
        # pattern so is hopefully unnecessary
        pattern = re.compile('href="#([^"]+)"')
        matches = [m for m in pattern.finditer(form.question_obj.question)]
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

        return context

    def test_func(self):
        role = self.get_project_role()
        return role.can_classify_data if role else False

    def done(self, form_list, **kwargs):
        """
        Called when the classification process is complete

        Record the user's classification and show results
        """
        tier = None
        questions = []
        for form in form_list:
            question = form.question_obj
            answer = form.cleaned_data['question']
            questions.append((question, answer))
            if 'tier' in form.cleaned_data:
                tier = form.cleaned_data['tier']
                break

        classification = self.object.classify_as(tier, self.request.user, questions)

        return self.render_result(classification)

    def render_result(self, classification):
        """
        Show the classification result, along with that of other users
        (and the project's final classification, if available yet)
        """
        self.object.calculate_tier()

        other_classifications = self.object.classifications.exclude(
            created_by=self.request.user)

        table = ClassificationOpinionQuestionTable(
            [classification] + list(other_classifications)
        )

        return render(self.request, 'projects/work_package_classify_results.html', {
            'classification': classification,
            'other_classifications': other_classifications,
            'project_tier': self.object.tier,
            'questions_table': table,
        })

    def get_form(self, *args, **kwargs):
        # Both SessionWizardView and SingleProjectMixin define a get_form function
        # SessionWizardView calls it a *lot*, and the definition in SingleProjectMixin
        # results in a database call that we really don't need
        return SessionWizardView.get_form(self, *args, **kwargs)


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
