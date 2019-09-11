from braces.forms import UserKwargModelFormMixin
from django.contrib.auth.mixins import UserPassesTestMixin


class UserPermissionRequiredMixin(UserPassesTestMixin):
    """
    View mixin to ensure only users with certain roles are able to access the view
    """
    user_permissions = []

    def test_func(self):
        try:
            for p in self.user_permissions:
                if getattr(self.request.user.user_role, p):
                    return True
        except AttributeError:
            return False


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
