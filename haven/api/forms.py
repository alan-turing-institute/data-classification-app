from django import forms
from oauth2_provider.models import Application
from sentry_sdk import capture_message

from haven.api.models import ApplicationProfile


class ApplicationCreateOrUpdateForm(forms.ModelForm):
    """A custom form for use in OAuth application management views"""

    maximum_tier = forms.IntegerField(initial=5, min_value=0, max_value=5)

    class Meta:
        model = Application
        fields = [
            "name",
            "client_id",
            "client_secret",
            "client_type",
            "authorization_grant_type",
            "redirect_uris",
            "algorithm",
        ]

    def save(self, commit=True):
        application = super().save(commit=commit)
        # Save `maximum_tier` information to `ApplicationProfile` model
        try:
            ApplicationProfile.objects.update_or_create(
                application=application,
                defaults={"maximum_tier": self.cleaned_data["maximum_tier"]},
            )
        except Exception:
            capture_message(
                f"Unable to save maximum tier to profile for application '{application.name}'"
            )
        return application
