from collections import OrderedDict

from braces.views import UserFormKwargsMixin
from crispy_forms.layout import Submit
from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import OuterRef, Subquery
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, FormMixin, UpdateView
from formtools.wizard.views import SessionWizardView

from data.forms import SingleQuestionForm
from data.models import ClassificationQuestion
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
    ProjectClassifyDeleteForm,
    ProjectForm,
)
from .models import ClassificationOpinion, Participant, Project
from .roles import ProjectRole
from .tables import ClassificationOpinionQuestionTable, PolicyTable


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
        participants = Participant.objects.filter(
            user=self.request.user, project=OuterRef('pk')
        )
        return super().get_queryset().\
            get_visible_projects(self.request.user).\
            annotate(your_role=Subquery(participants.values('role')[:1]))


class ProjectDetail(LoginRequiredMixin, SingleProjectMixin, DetailView):
    def get_context_data(self, **kwargs):
        project = self.get_object()
        kwargs['participant'] = self.request.user.get_participant(project)
        context = SingleProjectMixin.get_context_data(self, **kwargs)

        if project.has_tier:
            # Don't show these until we have a tier, to avoid influencing anybody that
            # hasn't classified yet
            policies = project.get_policies()
            context['policy_table'] = PolicyTable(policies)

            classifications = project.classifications.all()
            context['question_table'] = ClassificationOpinionQuestionTable(classifications)

        return context


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


class ProjectAddUser(
    LoginRequiredMixin, UserPassesTestMixin,
    UserFormKwargsMixin, SingleProjectMixin, FormMixin, DetailView
):
    template_name = 'projects/project_add_user.html'
    form_class = ProjectAddUserForm

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
        obj = self.get_object()
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
        kwargs['ordered_participants'] = self.get_object().ordered_participant_set()
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

    def get_context_data(self, **kwargs):
        helper = ParticipantInlineFormSetHelper()
        # Use crispy FormHelper to add submit and cancel buttons
        helper.add_input(Submit('submit', 'Save Changes'))
        helper.add_input(Submit('cancel', 'Cancel',
                                css_class='btn-secondary',
                                formnovalidate='formnovalidate'))
        helper.form_method = 'POST'
        kwargs['helper'] = helper

        kwargs['participants'] = self.get_object().ordered_participant_set()
        kwargs['project'] = self.get_object()
        if 'formset' not in kwargs:
            kwargs['formset'] = self.get_formset()
        return super().get_context_data(**kwargs)

    def get_formset(self, **kwargs):
        form_kwargs = {'user': self.request.user}
        if self.request.method == 'POST':
            return UsersForProjectInlineFormSet(
                self.request.POST,
                instance=self.get_object(),
                form_kwargs=form_kwargs,
                queryset=self.get_object().ordered_participant_set()
            )
        else:
            return UsersForProjectInlineFormSet(
                instance=self.get_object(),
                form_kwargs=form_kwargs,
                queryset=self.get_object().ordered_participant_set()
            )

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

    def post(self, request, *args, **kwargs):
        if "cancel" in request.POST:
            url = self.get_success_url()
            return HttpResponseRedirect(url)

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
        questions = []
        for form in form_list:
            question = form.fields['question'].label
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
            user=self.request.user)

        table = ClassificationOpinionQuestionTable(
            [classification] + list(other_classifications)
        )

        return render(self.request, 'projects/project_classify_results.html', {
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


class ProjectClassifyDelete(
    LoginRequiredMixin, UserPassesTestMixin,
    FormMixin, SingleProjectMixin, DetailView
):
    template_name = 'projects/project_classify_delete.html'
    form_class = ProjectClassifyDeleteForm

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
        return reverse('projects:detail', args=[self.object.id])


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
            existing_users = Project.objects.get(pk=project_id).participant_set.values('user')
            qs = User.objects.exclude(pk__in=existing_users)
        else:
            qs = User.objects.all()

        if self.q:
            qs = qs.filter(username__istartswith=self.q) | \
                 qs.filter(first_name__istartswith=self.q) | \
                 qs.filter(last_name__istartswith=self.q)

        return qs

    def get_result_label(self, user):
        return user.display_name()
