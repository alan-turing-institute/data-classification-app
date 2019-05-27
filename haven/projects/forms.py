from braces.forms import UserKwargModelFormMixin
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from data.models import Dataset
from django.urls import reverse
from identity.mixins import SaveCreatorMixin
from identity.models import User

from .models import Participant, Project
from .roles import ProjectRole


class ProjectForm(SaveCreatorMixin, forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']


class ProjectUserAutocompleteChoiceField(forms.ModelChoiceField):
    """Autocomplete field for adding users"""

    def __init__(self, project_id=None):
        """User choice should be restricted to users not yet in this project"""

        if project_id:
            autocomplete_url = reverse('projects:new_participant_autocomplete', kwargs={'pk': project_id})
        else:
            autocomplete_url = 'projects:new_participant_autocomplete/'

        widget = autocomplete.ModelSelect2(
            url=autocomplete_url,
            attrs={
                'data-placeholder': 'Search for user',
            },
        )
        super().__init__(queryset=User.objects.all(), widget=widget)


class ProjectAddUserForm(UserKwargModelFormMixin, forms.Form):
    """Form template for adding participants to a project"""

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop('project_id')
        super(ProjectAddUserForm, self).__init__(*args, **kwargs)

        # Update user field with project ID
        self.fields['username'] = ProjectUserAutocompleteChoiceField(project_id)

    # Use crispy FormHelper to add submit and cancel buttons
    helper = FormHelper()
    helper.add_input(Submit('submit', 'Add user'))
    helper.add_input(Submit('cancel', 'Cancel',
                                 css_class='btn-secondary',
                                 formnovalidate='formnovalidate'))
    helper.form_method = 'POST'

    username = ProjectUserAutocompleteChoiceField()

    role = forms.ChoiceField(
        choices=ProjectRole.choices(),
        help_text='Role on this project'
    )

    class Meta:
        model = User
        fields = ('__all__')

    def clean_username(self):
        username = self.cleaned_data['username']

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
        user = self.cleaned_data['username']
        return self.project.add_user(user, role, self.user)


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
    help_texts={'project': None, 'role': None},
)


class ProjectAddDatasetForm(SaveCreatorMixin, forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ('name', 'description')


class ProjectClassifyDeleteForm(SaveCreatorMixin, forms.Form):
    pass
