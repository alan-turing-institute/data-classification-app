from collections import OrderedDict

from braces.views import UserFormKwargsMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import OuterRef, Subquery
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, FormMixin
from formtools.wizard.views import SessionWizardView

from data.forms import SingleQuestionForm
from data.models import ClassificationQuestion
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


class ProjectClassifyData(
    LoginRequiredMixin, UserPassesTestMixin, SingleProjectMixin, SessionWizardView
):
    template_name = 'projects/project_classify_data.html'
    form_list = [
        ('_', SingleQuestionForm)
    ]

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
            # The condition needs to be true not just for the form to show, but
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

    def test_func(self):
        role = self.get_project_role()
        return role.can_classify_data if role else False

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

    def get_form(self, *args, **kwargs):
        # Both SessionWizardView and SingleProjectMixin define a get_form function
        # SessionWizardView calls it a *lot*, and the definition in SingleProjectMixin
        # results in a database call that we really don't need
        return SessionWizardView.get_form(self, *args, **kwargs)
