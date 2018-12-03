from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from .mixins import SaveCreatorMixin
from .models import User
from .remote import create_user


class CreateUserForm(SaveCreatorMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email address already exists")
        return email

    def save(self, **kwargs):
        self.instance.generate_username()

        if settings.USE_LDAP:
            create_user(self.instance)

        return super().save(**kwargs)
