from braces.forms import UserKwargModelFormMixin
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.urls import reverse

from data.models import Dataset
from identity.mixins import SaveCreatorMixin
from identity.models import User

from .models import (
    Participant,
    Project,
    WorkPackage,
    WorkPackageDataset,
    WorkPackageParticipant,
)
from .roles import ProjectRole


class SaveCancelFormHelper(FormHelper):
    def __init__(self, save_label='Save', save_class='btn-success', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_input(Submit('submit', save_label, css_class=save_class))
        self.add_input(Submit('cancel', 'Cancel', css_class='btn-secondary',
                              formnovalidate='formnovalidate'))


class ParticipantInlineFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_tag = False
        self.template = 'projects/includes/participants_inline_formset.html'


class ProjectForm(SaveCreatorMixin, forms.ModelForm):
    helper = SaveCancelFormHelper('Save Project')

    class Meta:
        model = Project
        fields = ['name', 'description']


class ProjectUserAutocompleteChoiceField(forms.ModelChoiceField):
    """Autocomplete field for adding users"""

    def __init__(self, project_id=None, *args, **kwargs):
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
        super().__init__(queryset=User.objects.all(), widget=widget, *args, **kwargs)


class ProjectAddUserForm(UserKwargModelFormMixin, forms.ModelForm):
    """Form template for adding participants to a project"""

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop('project_id')
        super(ProjectAddUserForm, self).__init__(*args, **kwargs)

        # Update user field with project ID
        self.fields['user'] = ProjectUserAutocompleteChoiceField(project_id, label='Username')

    user = ProjectUserAutocompleteChoiceField(label='Username')

    role = forms.ChoiceField(
        choices=ProjectRole.choices(),
        help_text='Role on this project'
    )

    class Meta:
        model = Participant
        fields = ('user', 'role')

    def clean_user(self):
        username = self.cleaned_data['user']

        # Verify if user already exists on project
        if self.project.participants.filter(
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
        user = self.cleaned_data['user']
        return self.project.add_user(user, role, self.user)


class WorkPackageForParticipantInlineForm(SaveCreatorMixin, forms.ModelForm):
    """Inline form describing a single user/role assignment on a work package"""
    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['work_package'].queryset = project.work_packages

    class Meta:
        model = WorkPackageParticipant
        fields = ('work_package',)


WorkPackagesForParticipantInlineFormSet = inlineformset_factory(
    Participant,
    WorkPackageParticipant,
    form=WorkPackageForParticipantInlineForm,
    fk_name='participant',
    extra=1,
    can_delete=True,
    help_texts={'work_package': None},
)


class ProjectForUserInlineForm(SaveCreatorMixin, forms.ModelForm):
    """Inline form describing a single user/role assignment on a project"""
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
        return self.cleaned_data


ProjectsForUserInlineFormSet = inlineformset_factory(
    User,
    Participant,
    form=ProjectForUserInlineForm,
    fk_name='user',
    extra=1,
    can_delete=True,
    help_texts={'project': None, 'role': None},
)


class UserForProjectInlineForm(SaveCreatorMixin, forms.ModelForm):
    """Inline form describing a single project/role assignment for a user"""
    def __init__(self, assignable_roles=None, *args, **kwargs):
        super(UserForProjectInlineForm, self).__init__(*args, **kwargs)
        if assignable_roles:
            self.fields['role'].choices = [
                (role, name)
                for role, name in self.fields['role'].choices
                if not role or role in assignable_roles
            ]

    class Meta:
        model = Participant
        fields = ('role',)

    def project_user(self):
        return self.instance.user

    def clean_role(self):
        role = self.cleaned_data['role']
        if 'role' in self.changed_data:
            project = self.instance.project
            role_model = ProjectRole(self.cleaned_data['role'])
            if not self.user.project_role(project).can_assign_role(role_model):
                raise ValidationError("You cannot assign role " +
                                      ProjectRole.display_name(role) +
                                      " for this project")
        return role


UsersForProjectInlineFormSet = inlineformset_factory(
    Project,
    Participant,
    form=UserForProjectInlineForm,
    fk_name='project',
    extra=0,
    can_delete=True,
    help_texts={'role': None},
)


class ProjectAddDatasetForm(SaveCreatorMixin, forms.ModelForm):
    helper = SaveCancelFormHelper('Create Dataset')

    class Meta:
        model = Dataset
        fields = ('name', 'description', 'default_representative')

    def __init__(self, *args, **kwargs):
        representative_qs = kwargs.pop('representative_qs')
        super().__init__(*args, **kwargs)
        self.fields['default_representative'].queryset = representative_qs


class ProjectAddWorkPackageForm(UserKwargModelFormMixin, forms.ModelForm):
    helper = SaveCancelFormHelper('Create Work Package')

    class Meta:
        model = WorkPackage
        fields = ('name', 'description')


class WorkPackageAddDatasetForm(SaveCreatorMixin, forms.ModelForm):
    helper = SaveCancelFormHelper('Add Dataset to Work Package')

    class Meta:
        model = WorkPackageDataset
        fields = ('dataset',)

    def __init__(self, work_package, *args, **kwargs):
        kwargs.setdefault('instance', WorkPackageDataset(work_package=work_package))
        super().__init__(*args, **kwargs)
        self.fields['dataset'].queryset = work_package.project.datasets


class WorkPackageAddParticipantForm(SaveCreatorMixin, forms.ModelForm):
    helper = SaveCancelFormHelper('Add Participant to Work Package')

    class Meta:
        model = WorkPackageParticipant
        fields = ('participant',)

    def __init__(self, work_package, *args, **kwargs):
        kwargs.setdefault('instance', WorkPackageParticipant(work_package=work_package))
        super().__init__(*args, **kwargs)
        self.fields['participant'].queryset = work_package.project.participants


class WorkPackageClassifyDeleteForm(SaveCreatorMixin, forms.Form):
    helper = SaveCancelFormHelper('Delete Classification', 'btn-danger')
    helper.form_method = 'POST'
