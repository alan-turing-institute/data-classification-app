from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget

from identity.roles import UserRole
from .mixins import SaveCreatorMixin
from .models import User


class CreateUserForm(SaveCreatorMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['role', 'email', 'first_name', 'last_name', 'mobile']
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
        if 'role' in self.changed_data:
            role_model = UserRole(self.cleaned_data['role'])
            if not UserRole(self.user.role).can_assign_role(role_model):
                raise ValidationError("You cannot assign role " + UserRole.display_name(role))
        return role

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("There is already a user with this email address.")
        return email

    def save(self, **kwargs):
        self.instance.generate_username()

        return super().save(**kwargs)
