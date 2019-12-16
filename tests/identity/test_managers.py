import pytest

from haven.identity.models import User


@pytest.mark.django_db
class TestCustomUserManager:
    def test_get_visible_users(self, programme_manager, standard_user, system_manager):
        assert list(User.objects.get_visible_users(standard_user)) == []
        assert list(User.objects.get_visible_users(programme_manager)) == [programme_manager, standard_user, system_manager]
        assert list(User.objects.get_visible_users(system_manager)) == [programme_manager, standard_user, system_manager]

    def test_get_by_natural_key(self):
        username_lower = 'test.user@example.com'
        username_upper = 'TEST.USER@EXAMPLE.COM'
        username_mixed = 'Test.User@Example.Com'

        # Check that no user is returned if no match
        with pytest.raises(User.DoesNotExist):
            User.objects.get_by_natural_key(username_lower)
        with pytest.raises(User.DoesNotExist):
            User.objects.get_by_natural_key(username_upper)
        with pytest.raises(User.DoesNotExist):
            User.objects.get_by_natural_key(username_mixed)

        # A user with a case insensitive match will always be returned
        user_lowercase = User.objects.create_user(first_name='testl', last_name='testl', username=username_lower)
        assert User.objects.get_by_natural_key(username_lower) == user_lowercase
        assert User.objects.get_by_natural_key(username_upper) == user_lowercase
        assert User.objects.get_by_natural_key(username_mixed) == user_lowercase

        # A case-sensitive match will take priority
        user_uppercase = User.objects.create_user(first_name='testm', last_name='testm', username=username_upper)
        user_mixedcase = User.objects.create_user(first_name='testm', last_name='testm', username=username_mixed)
        assert User.objects.get_by_natural_key(username_lower) == user_lowercase
        assert User.objects.get_by_natural_key(username_upper) == user_uppercase
        assert User.objects.get_by_natural_key(username_mixed) == user_mixedcase
