from braces.forms import UserKwargModelFormMixin
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget

from haven.identity.mixins import SaveCreatorMixin
from haven.identity.models import User
from haven.identity.roles import UserRole


class EditUserForm(UserKwargModelFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "mobile", "email", "role"]
        widgets = {
            "mobile": PhoneNumberInternationalFallbackWidget(
                region=settings.PHONENUMBER_DEFAULT_REGION,
                attrs={"class": "form-control"},
            ),
        }
        labels = {
            "mobile": "Mobile phone number",
        }
        help_texts = {
            "mobile": "International numbers must start with +",
        }
        error_messages = {
            "mobile": {
                "required": "A mobile phone number is required.",
                "invalid": "Enter a valid UK or international phone number.",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assignable_roles = [r.value for r in self.user.system_permissions.creatable_roles]

        # Hide the role field if the only allowable role is standard user
        if assignable_roles and assignable_roles != [UserRole.NONE.value]:
            self.fields["role"].choices = [
                (role, name)
                for role, name in self.fields["role"].choices
                if not role or role in assignable_roles
            ]
        else:
            del self.fields["role"]

    def clean_role(self):
        role = self.cleaned_data["role"]
        role_model = UserRole(role)
        role_display = UserRole.display_name(role)
        if "role" in self.changed_data:
            if not self.user.system_permissions.can_assign_role(role_model):
                raise ValidationError(f"You cannot assign the role {role_display}")
        else:
            if not self.user.system_permissions.can_assign_role(role_model):
                raise ValidationError(f"You cannot edit users with the role {role_display}")
        return role

    def clean_email(self):
        email = self.cleaned_data["email"]
        if "email" in self.changed_data:
            if User.objects.filter(email=email).exists():
                raise ValidationError("There is already a user with this email address.")
        return email

    def clean(self):
        super().clean()
        if self.instance:
            role_model = self.instance.user_role
            role_display = UserRole.display_name(self.instance.role)
            if not self.user.system_permissions.can_assign_role(role_model):
                raise ValidationError(f"You cannot edit users with the role {role_display}")


class CreateUserForm(SaveCreatorMixin, EditUserForm):
    def save(self, **kwargs):
        self.instance.generate_username()

        return super().save(**kwargs)
