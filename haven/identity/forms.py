from django import forms
from django.conf import settings

from .mixins import SaveCreatorMixin
from .models import User
from .remote import create_user


class CreateUserForm(SaveCreatorMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name']

    def save(self, **kwargs):
        self.instance.generate_username()

        if settings.USE_LDAP:
            create_user(self.instance)

        return super().save(**kwargs)
