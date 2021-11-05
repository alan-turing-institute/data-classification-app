from braces.forms import UserKwargModelFormMixin
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.urls import reverse

from haven.core.forms import InlineFormSetHelper
from haven.data.models import Dataset
from haven.identity.mixins import SaveCreatorMixin
from haven.identity.models import User
from haven.projects.models import (
    Participant,
    Project,
    WorkPackage,
    WorkPackageDataset,
    WorkPackageParticipant,
)
from haven.projects.roles import ProjectRole


# Widgets


class ShowValue(forms.Widget):
    """
    Dummy widget that simply displays the relevant value.

    This is only necessary for forms used in inline formsets - for others, it's better to use
    the Layout object to display any text.

    Should only be used with disabled fields, since it won't actually submit a value.
    """

    template_name = "includes/show_value_widget.html"


# Fields


class UserAutocompleteChoiceField(forms.ModelChoiceField):
    """Autocomplete field for adding users"""

    def __init__(self, autocomplete_url=None, *args, **kwargs):
        """User choice should be restricted to users not yet in this project"""

        autocomplete_url = autocomplete_url or "dummy_url"

        widget = autocomplete.ModelSelect2(
            url=autocomplete_url, attrs={"data-placeholder": "Search for user",},
        )
        super().__init__(queryset=User.objects.all(), widget=widget, *args, **kwargs)


# Helpers


class SaveCancelFormHelper(FormHelper):
    def __init__(self, save_label="Save", save_class="btn-success", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_input(Submit("submit", save_label, css_class=save_class))
        self.add_input(
            Submit(
                "cancel",
                "Cancel",
                css_class="btn-secondary",
                formnovalidate="formnovalidate",
            )
        )


class SaveCancelInlineFormSetHelper(InlineFormSetHelper):
    def __init__(self, save_label="Save", save_class="btn-success", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_input(Submit("submit", save_label, css_class=save_class))
        self.add_input(
            Submit(
                "cancel",
                "Cancel",
                css_class="btn-secondary",
                formnovalidate="formnovalidate",
            )
        )


class ParticipantInlineFormSetHelper(SaveCancelInlineFormSetHelper):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("save_label", "Save Participants")
        super().__init__(*args, **kwargs)
        self.form_tag = False
        self.template = "projects/includes/participants_inline_formset.html"


# Forms


class ParticipantForm(UserKwargModelFormMixin, forms.ModelForm):
    """Form template for editing participants on a project"""

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop("project_id")
        super().__init__(*args, **kwargs)

        project = Project.objects.get(pk=project_id)
        self.fields["work_packages"].queryset = project.work_packages

    role = forms.ChoiceField(
        choices=ProjectRole.choices(), help_text="Role on this project"
    )

    work_packages = forms.ModelMultipleChoiceField(
        queryset=WorkPackage.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Participant
        fields = ("role", "work_packages")

    def save(self, *args, **kwargs):
        participant = super().save(*args, **kwargs)
        wpps = WorkPackageParticipant.objects.filter(participant=participant)
        existing = set([wpp.work_package for wpp in wpps])
        desired = set(self.cleaned_data["work_packages"])
        removed = existing - desired
        added = desired - existing
        wpps.filter(work_package__in=removed).delete()
        for wp in added:
            WorkPackageParticipant.objects.create(
                participant=participant, work_package=wp, created_by=self.user
            )
        return participant


class ProjectForm(SaveCreatorMixin, forms.ModelForm):
    helper = SaveCancelFormHelper("Save Project")

    class Meta:
        model = Project
        fields = ["name", "description", "programmes"]
        labels = {
            "programmes": "Programmes",
        }
        help_texts = {
            "programmes": "",
        }
        widgets = {"programmes": autocomplete.TaggitSelect2("dummy_url")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["programmes"].widget.url = reverse(
            "projects:autocomplete_programme"
        )


class ProjectAddDatasetForm(SaveCreatorMixin, forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ("name", "description", "default_representative")

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop("project_id")
        super().__init__(*args, **kwargs)
        autocomplete_url = reverse(
            "projects:autocomplete_dpr", kwargs={"pk": project_id}
        )
        field = UserAutocompleteChoiceField(
            autocomplete_url, label="Default Representative"
        )
        self.fields["default_representative"] = field

        self.project = Project.objects.get(pk=project_id)
        self.fields[
            "work_packages"
        ].queryset = self.project.work_packages.filter_by_permission("add_datasets")

    work_packages = forms.ModelMultipleChoiceField(
        queryset=WorkPackage.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def save(self, *args, **kwargs):
        dataset = super().save(*args, **kwargs)
        self.project.add_dataset(dataset, dataset.default_representative, self.user)
        for wp in self.cleaned_data["work_packages"]:
            wp.add_dataset(dataset, self.user)
        return dataset


class ProjectEditDatasetForm(forms.ModelForm):
    helper = SaveCancelFormHelper("Save Dataset")

    class Meta:
        model = Dataset
        fields = ("name", "description")


class ProjectEditDatasetDPRForm(UserKwargModelFormMixin, forms.ModelForm):
    helper = SaveCancelFormHelper("Save Dataset")

    class Meta:
        model = Dataset
        fields = ("default_representative",)

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop("project_id")
        super().__init__(*args, **kwargs)
        autocomplete_url = reverse(
            "projects:autocomplete_dpr", kwargs={"pk": project_id}
        )
        field = UserAutocompleteChoiceField(
            autocomplete_url, label="Default Representative"
        )
        self.fields["default_representative"] = field

    def save(self, *args, **kwargs):
        dataset = super().save(*args, **kwargs)
        self.project.update_representative(dataset, self.user)
        return dataset


class ProjectDeleteDatasetForm(forms.Form):
    helper = SaveCancelFormHelper("Delete Dataset", "btn-danger")
    helper.form_method = "POST"


class ProjectAddUserForm(UserKwargModelFormMixin, forms.ModelForm):
    """Form template for adding participants to a project"""

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop("project_id")
        super(ProjectAddUserForm, self).__init__(*args, **kwargs)

        # Update user field with project ID
        autocomplete_url = reverse(
            "projects:autocomplete_new_participant", kwargs={"pk": project_id}
        )
        self.fields["user"] = UserAutocompleteChoiceField(
            autocomplete_url, label="Username"
        )

        project = Project.objects.get(pk=project_id)
        self.fields["work_packages"].queryset = project.work_packages

    user = UserAutocompleteChoiceField(label="Username")

    role = forms.ChoiceField(
        choices=ProjectRole.choices(), help_text="Role on this project"
    )

    work_packages = forms.ModelMultipleChoiceField(
        queryset=WorkPackage.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Participant
        fields = ("user", "role", "work_packages")

    def clean_user(self):
        username = self.cleaned_data["user"]

        # Verify if user already exists on project
        if self.project.participants.filter(user__username=username).exists():
            raise ValidationError("User is already on project")

        # Do not allow user to be added unless they have already been created
        # in the database
        if not User.objects.filter(username=username).exists():
            raise ValidationError("Username not known")
        return username

    def save(self, **kwargs):
        role = self.cleaned_data["role"]
        user = self.cleaned_data["user"]
        work_packages = self.cleaned_data["work_packages"]
        return self.project.add_user(
            user, role, work_packages=work_packages, created_by=self.user
        )


class ProjectAddWorkPackageForm(UserKwargModelFormMixin, forms.ModelForm):
    class Meta:
        model = WorkPackage
        fields = ("name", "description")

    def __init__(self, *args, **kwargs):
        project_id = kwargs.pop("project_id")
        super().__init__(*args, **kwargs)
        self.project = Project.objects.get(pk=project_id)
        self.fields["datasets"].queryset = self.project.datasets

    datasets = forms.ModelMultipleChoiceField(
        queryset=Dataset.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def save(self, *args, **kwargs):
        work_package = WorkPackage(
            name=self.cleaned_data["name"], description=self.cleaned_data["description"]
        )
        self.project.add_work_package(work_package, self.user)
        for dataset in self.cleaned_data["datasets"]:
            work_package.add_dataset(dataset, self.user)
        return work_package


class WorkPackageEditForm(UserKwargModelFormMixin, forms.ModelForm):
    helper = SaveCancelFormHelper("Save Work Package")

    class Meta:
        model = WorkPackage
        fields = ("name", "description")


class WorkPackageDeleteForm(forms.Form):
    helper = SaveCancelFormHelper("Delete Work Package", "btn-danger")
    helper.form_method = "POST"


class ProjectArchiveForm(forms.Form):
    helper = SaveCancelFormHelper("Archive Project", "btn-danger")
    helper.form_method = "POST"


class WorkPackageAddDatasetForm(SaveCreatorMixin, forms.ModelForm):
    helper = SaveCancelFormHelper("Add Dataset to Work Package")

    class Meta:
        model = WorkPackageDataset
        fields = ("dataset",)

    def __init__(self, work_package, *args, **kwargs):
        kwargs.setdefault("instance", WorkPackageDataset(work_package=work_package))
        super().__init__(*args, **kwargs)
        qs = work_package.project.datasets.exclude(id__in=work_package.datasets.all())
        self.fields["dataset"].queryset = qs


class WorkPackageAddParticipantForm(SaveCreatorMixin, forms.ModelForm):
    helper = SaveCancelFormHelper("Add Participant to Work Package")

    class Meta:
        model = WorkPackageParticipant
        fields = ("participant",)

    def __init__(self, work_package, *args, **kwargs):
        kwargs.setdefault("instance", WorkPackageParticipant(work_package=work_package))
        super().__init__(*args, **kwargs)
        qs = work_package.project.participants
        qs = qs.exclude(pk__in=work_package.participants.all())
        self.fields["participant"].queryset = qs


class WorkPackageClearForm(SaveCreatorMixin, forms.Form):
    helper = SaveCancelFormHelper("Clear Classifications", "btn-danger")
    helper.form_method = "POST"


class WorkPackageClassifyDeleteForm(SaveCreatorMixin, forms.Form):
    helper = SaveCancelFormHelper("Delete Classification", "btn-danger")
    helper.form_method = "POST"


class WorkPackageClassifyCloseForm(forms.Form):
    helper = SaveCancelFormHelper("Close Classification", "btn-danger")
    helper.form_method = "POST"


class WorkPackageClassifyOpenForm(forms.Form):
    helper = SaveCancelFormHelper("Open Classification", "btn-danger")
    helper.form_method = "POST"


# Inline forms


class DatasetForWorkPackageInlineForm(UserKwargModelFormMixin, forms.ModelForm):
    """Inline form describing a single work package assignment for a dataset"""

    name = forms.CharField(disabled=True, widget=ShowValue, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        if instance:
            self.fields["name"].initial = instance.dataset.name

    class Meta:
        model = WorkPackageDataset
        fields = ()


class ParticipantForWorkPackageInlineForm(UserKwargModelFormMixin, forms.ModelForm):
    """Inline form describing a single work package assignment for a user"""

    username = forms.CharField(disabled=True, widget=ShowValue, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        if instance:
            self.fields["username"].initial = instance.participant.user.username

    class Meta:
        model = Participant
        fields = ()


class ParticipantForWorkPackageApprovalInlineForm(ParticipantForWorkPackageInlineForm):
    """Inline form describing a single work package assignment for a user"""

    approved = forms.BooleanField(required=False)

    def save(self, **kwargs):
        if self.cleaned_data["approved"]:
            self.instance.approve(self.user)


class ProjectForUserInlineForm(SaveCreatorMixin, forms.ModelForm):
    """Inline form describing a single user/role assignment on a project"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project"].queryset = Project.objects.get_editable_projects(
            self.user
        )

    class Meta:
        model = Participant
        fields = ("project", "role")

    def clean(self):
        if "project" in self.cleaned_data and "role" in self.cleaned_data:
            project = self.cleaned_data["project"]
            role = ProjectRole(self.cleaned_data["role"])
            if not self.user.project_permissions(project).can_assign_role(role):
                raise ValidationError("You cannot assign the role on this project")
        return self.cleaned_data


class UserForProjectInlineForm(SaveCreatorMixin, forms.ModelForm):
    """Inline form describing a single project/role assignment for a user"""

    def __init__(self, assignable_roles=None, *args, **kwargs):
        super(UserForProjectInlineForm, self).__init__(*args, **kwargs)
        if assignable_roles:
            self.fields["role"].choices = [
                (role, name)
                for role, name in self.fields["role"].choices
                if not role or role in assignable_roles
            ]

    class Meta:
        model = Participant
        fields = ("role",)

    def project_user(self):
        return self.instance.user

    def clean_role(self):
        role = self.cleaned_data["role"]
        if "role" in self.changed_data:
            project = self.instance.project
            role_model = ProjectRole(self.cleaned_data["role"])
            if not self.user.project_permissions(project).can_assign_role(role_model):
                raise ValidationError(
                    "You cannot assign the role "
                    + ProjectRole.display_name(role)
                    + " for this project"
                )
        return role


# Form factories

DatasetsForWorkPackageInlineFormSet = inlineformset_factory(
    WorkPackage,
    WorkPackageDataset,
    form=DatasetForWorkPackageInlineForm,
    fk_name="work_package",
    extra=0,
    can_delete=True,
)


ParticipantsForWorkPackageInlineFormSet = inlineformset_factory(
    WorkPackage,
    WorkPackageParticipant,
    form=ParticipantForWorkPackageInlineForm,
    fk_name="work_package",
    extra=0,
    can_delete=True,
)


ParticipantsForWorkPackageApprovalInlineFormSet = inlineformset_factory(
    WorkPackage,
    WorkPackageParticipant,
    form=ParticipantForWorkPackageApprovalInlineForm,
    fk_name="work_package",
    extra=0,
    can_delete=False,
)


ProjectsForUserInlineFormSet = inlineformset_factory(
    User,
    Participant,
    form=ProjectForUserInlineForm,
    fk_name="user",
    extra=1,
    can_delete=True,
    help_texts={"project": None, "role": None},
)


UsersForProjectInlineFormSet = inlineformset_factory(
    Project,
    Participant,
    form=UserForProjectInlineForm,
    fk_name="project",
    extra=0,
    can_delete=True,
    help_texts={"role": None},
)
