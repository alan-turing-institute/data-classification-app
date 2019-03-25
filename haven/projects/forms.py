from braces.forms import UserKwargModelFormMixin
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from data.models import Dataset
from identity.mixins import SaveCreatorMixin
from identity.models import User

from .models import Participant, Project
from .roles import ProjectRole


class ProjectForm(SaveCreatorMixin, forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']


class ProjectAddUserForm(UserKwargModelFormMixin, forms.Form):
    username = forms.CharField(help_text='Username')
    role = forms.ChoiceField(
        choices=ProjectRole.choices(),
        help_text='Role on this project'
    )

    def clean_username(self):
        username = self.cleaned_data['username']

        # Allow adding username without the domain
        if not '@' in username:
            username = '{username}@{domain}'.format(
                username=username,
                domain=settings.SAFE_HAVEN_DOMAIN
            )

        # Verify if user already exists on project
        if self.project.participant_set.filter(
            user__username=username
        ).exists():
            raise ValidationError("User is already on project")

        # Do not allow user to be added unless they have already been created
        # in the database
        if not User.objects.filter(
            username=username
        ).exists():
            raise ValidationError("Username not known")
        return username

    def save(self, **kwargs):
        role = self.cleaned_data['role']
        username = self.cleaned_data['username']
        return self.project.add_user(username, role, self.user)


class ProjectForUserInlineForm(SaveCreatorMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = Project.objects.get_editable_projects(self.user)

    class Meta:
        model = Participant
        fields = ('project', 'role')

    def clean(self):
        if 'project' in self.cleaned_data:
            project = self.cleaned_data['project']
            role = ProjectRole(self.cleaned_data['role'])
            if not self.user.project_role(project).can_assign_role(role):
                raise ValidationError("You cannot assign the role on this project")


ProjectsForUserInlineFormSet = inlineformset_factory(
    User,
    Participant,
    form=ProjectForUserInlineForm,
    fk_name='user',
    extra=1,
    can_delete=True,
)


class ProjectAddDatasetForm(SaveCreatorMixin, forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ('name', 'description')
