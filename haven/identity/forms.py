from braces.forms import UserKwargModelFormMixin
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget

from identity.roles import UserRole

from .mixins import SaveCreatorMixin
from .models import User


class EditUserForm(UserKwargModelFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'mobile', 'email', 'role']
        widgets = {
            'mobile': PhoneNumberInternationalFallbackWidget(
                region=settings.PHONENUMBER_DEFAULT_REGION,
                attrs={'class': 'form-control'}),
        }
        labels = {
            'mobile': 'Mobile phone number',
        }
        help_texts = {
            'mobile': 'International numbers must start with +',
        }
        error_messages = {
            'mobile': {
                'required': 'A mobile phone number is required.',
                'invalid': 'Enter a valid UK or international phone number.',
            },
        }

    def clean_role(self):
        role = self.cleaned_data['role']
        role_model = UserRole(role)
        role_display = UserRole.display_name(role)
        if 'role' in self.changed_data:
            if not UserRole(self.user.role).can_assign_role(role_model):
                raise ValidationError(f"You cannot assign role {role_display}")
        else:
            if not UserRole(self.user.role).can_assign_role(role_model):
                raise ValidationError(f"You cannot edit users with role {role_display}")
        return role

    def clean_email(self):
        email = self.cleaned_data['email']
        if 'email' in self.changed_data:
            if User.objects.filter(email=email).exists():
                raise ValidationError("There is already a user with this email address.")
        return email


class CreateUserForm(SaveCreatorMixin, EditUserForm):

    def save(self, **kwargs):
        self.instance.generate_username()

        return super().save(**kwargs)
