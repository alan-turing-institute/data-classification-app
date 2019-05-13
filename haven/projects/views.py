from braces.views import UserFormKwargsMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import OuterRef, Subquery
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, FormMixin
from formtools.wizard.views import SessionWizardView

from data.forms import Tier0Form, Tier1Form, Tier2Form, Tier3Form
from identity.mixins import UserRoleRequiredMixin
from identity.roles import UserRole

from .forms import ProjectAddDatasetForm, ProjectAddUserForm, ProjectForm
from .models import ClassificationOpinion, Participant, Project
from .roles import ProjectRole


class SingleProjectMixin(SingleObjectMixin):
    model = Project

    def get_queryset(self):
        return super().get_queryset().get_visible_projects(self.request.user)

    def get_project_role(self):
        """Return the logged in user's administrative role on the project"""
        return self.request.user.project_role(self.get_object())

    def get_project_participation_role(self):
        """Return the logged in user's assigned role on the project"""
        return self.request.user.project_participation_role(self.get_object())

    def get_context_data(self, **kwargs):
        kwargs['project_role'] = self.get_project_role()
        kwargs['project_participation_role'] = self.get_project_participation_role()
        return super().get_context_data(**kwargs)

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        form.project = self.get_object()
        return form


class ProjectCreate(
    LoginRequiredMixin, UserRoleRequiredMixin,
    UserFormKwargsMixin, CreateView
):
    model = Project
    form_class = ProjectForm

    user_roles = [UserRole.SYSTEM_CONTROLLER, UserRole.RESEARCH_COORDINATOR]

    def get_success_url(self):
        return reverse('projects:list')


class ProjectList(LoginRequiredMixin, ListView):
    context_object_name = 'projects'
    model = Project

    def get_queryset(self):
        # Store the user's project role on each participant
        participants = Participant.objects.filter(
            user=self.request.user, project=OuterRef('pk')
        )
        return super().get_queryset().\
            get_visible_projects(self.request.user).\
            annotate(your_role=Subquery(participants.values('role')[:1]))


class ProjectDetail(LoginRequiredMixin, SingleProjectMixin, DetailView):
    def get_context_data(self, **kwargs):
        kwargs['participant'] = self.request.user.get_participant(self.get_object())
        return super().get_context_data(**kwargs)


class ProjectAddUser(
    LoginRequiredMixin, UserPassesTestMixin,
    UserFormKwargsMixin, SingleProjectMixin, FormMixin, DetailView
):
    template_name = 'projects/project_add_user.html'
    form_class = ProjectAddUserForm

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
        obj = self.get_object()
        if self.get_project_role().can_list_participants:
            return reverse('projects:list_participants', args=[obj.id])
        else:
            return reverse('projects:detail', args=[obj.id])

    def test_func(self):
        return self.get_project_role().can_add_participants

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        self.object = self.get_object()
        if form.is_valid():
            form.save()
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
        kwargs['participants'] = self.get_object().participant_set.all()
        return super().get_context_data(**kwargs)


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

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        self.object = self.get_object()
        if form.is_valid():
            dataset = form.save()
            self.object.add_dataset(dataset)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def test_func(self):
        return self.get_project_role().can_add_datasets

    def get_success_url(self):
        return reverse('projects:detail', args=[self.get_object().id])


def _has_tier(wizard, previous_steps):
    """
    Have any of the previous steps yielded a 'tier' data field (i.e.
    determined definitively which tier the data is?
    """
    return not any(
        'tier' in (wizard.get_cleaned_data_for_step(step) or {})
        for step in previous_steps
    )


def show_tier_1(wizard):
    """
    Determine whether to show the tier 1 questions form

    If the tier0 form yielded a definitive result, then don't.
    """
    return _has_tier(wizard, ['tier0'])


def show_tier_2(wizard):
    """
    Determine whether to show the tier 2 questions form

    If the tier0 or tier1 forms yielded a definitive result, then don't.
    """
    return _has_tier(wizard, ['tier0', 'tier1'])


def show_tier_3(wizard):
    """
    Determine whether to show the tier 3 questions form

    If the tier0, tier1 or tier2 forms yielded a definitive result, then don't.
    """
    return _has_tier(wizard, ['tier0', 'tier1', 'tier2'])


class ProjectClassifyData(
    LoginRequiredMixin, UserPassesTestMixin, SingleProjectMixin, SessionWizardView
):
    template_name = 'projects/project_classify_data.html'

    form_list = [
        ('tier0', Tier0Form),
        ('tier1', Tier1Form),
        ('tier2', Tier2Form),
        ('tier3', Tier3Form),
    ]

    """
    Form wizard control logic: determine whether to show a given form, based
    on previous inputs.
    """
    condition_dict = {
        'tier1': show_tier_1,
        'tier2': show_tier_2,
        'tier3': show_tier_3,
    }

    def dispatch(self, *args, **kwargs):
        """
        Before doing anything on this view, determine whether this user has
        already classified the project.

        If they have, then show their classification (and others) rather than
        display the form again.
        """
        if self.request.user.is_authenticated:
            self.object = self.get_object()

            classification = ClassificationOpinion.objects.filter(
                project=self.object,
                user=self.request.user
            ).first()
            if classification:
                return self.render_result(classification)

        return super().dispatch(*args, *kwargs)

    def test_func(self):
        return self.get_project_participation_role().can_classify_data

    def done(self, form_list, **kwargs):
        """
        Called when the classification process is complete

        Record the user's classification and show results
        """
        tier = None
        for form in form_list:
            if 'tier' in form.cleaned_data:
                tier = form.cleaned_data['tier']
                break

        classification = self.object.classify_as(tier, self.request.user)

        return self.render_result(classification)

    def render_result(self, classification):
        """
        Show the classification result, along with that of other users
        (and the project's final classification, if available yet)
        """
        other_classifications = self.object.classifications.exclude(
            user=self.request.user)

        self.object.calculate_tier()

        return render(self.request, 'projects/project_classify_results.html', {
            'classification': classification,
            'other_classifications': other_classifications,
            'project_tier': self.object.tier,
        })
