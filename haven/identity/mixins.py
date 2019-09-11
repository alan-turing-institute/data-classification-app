from braces.forms import UserKwargModelFormMixin
from django.contrib.auth.mixins import UserPassesTestMixin


class SaveCreatorMixin(UserKwargModelFormMixin):
    """
    Form mixin to record the user that created an object

    Must be used on a `ModelForm` on which the model class has a `created_by`
    foreign key to `identity.User`
    """
    def save(self, **kwargs):
        obj = super().save(commit=False)
        obj.created_by = self.user
        obj.save()
        self.save_m2m()
        return obj
