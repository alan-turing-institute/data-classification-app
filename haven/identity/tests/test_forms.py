import pytest

from identity.forms import CreateUserForm
from identity.models import User


@pytest.mark.django_db
class TestCreateUserForm:
    def test_create_user(self, system_controller, settings):
        settings.SAFE_HAVEN_DOMAIN = 'example.com'
        form = CreateUserForm({
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'mobile': '+443338888888',
        }, user=system_controller)
        assert form.is_valid()

        form_user = form.save()

        form_user.refresh_from_db()
        assert form_user.created_by == system_controller
        assert form_user.username == 'test.user@example.com'

    def test_create_user_with_uk_phone(self, system_controller, settings):
        settings.SAFE_HAVEN_DOMAIN = 'example.com'
        form = CreateUserForm({
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'mobile': '01234567890',
        }, user=system_controller)
        assert form.is_valid()
        assert form.cleaned_data['mobile'] == '+441234567890'

        form_user = form.save()

        form_user.refresh_from_db()
        assert form_user.created_by == system_controller
        assert form_user.username == 'test.user@example.com'

    def test_create_user_with_international_format(self, system_controller, settings):
        settings.SAFE_HAVEN_DOMAIN = 'example.com'
        form = CreateUserForm({
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'mobile': '+1-541-754-3010',
        }, user=system_controller)
        assert form.is_valid()
        assert form.cleaned_data['mobile'] == '+15417543010'

        form_user = form.save()

        form_user.refresh_from_db()
        assert form_user.created_by == system_controller
        assert form_user.username == 'test.user@example.com'

    def test_retries_duplicate_username(self, system_controller, settings):
        settings.SAFE_HAVEN_DOMAIN = 'example.com'
        User.objects.create_user(email='a@b.com', username='test.user@example.com')
        User.objects.create_user(email='c@d.com', username='test.user1@example.com')
        form = CreateUserForm({
            'email': 'e@f.com',
            'first_name': 'Test',
            'last_name': 'User',
            'mobile': '+443338888888',
        }, user=system_controller)

        assert form.is_valid()
        form_user = form.save()

        assert form_user.username == 'test.user2@example.com'

    def test_form_invalid_if_duplicate_email_address(self, system_controller):
        # Ensure email uniqueness is checked at the form level rather than
        # raising integrity errors when writing to the db
        User.objects.create_user(email='a@b.com', username='test.user@example.com')
        form = CreateUserForm({
            'email': 'a@b.com',
            'first_name': 'Test',
            'last_name': 'User',
        }, user=system_controller)

        assert not form.is_valid()
        assert 'email' in form.errors

    def test_form_invalid_if_uk_number_invalid(self, system_controller, settings):
        settings.SAFE_HAVEN_DOMAIN = 'example.com'
        form = CreateUserForm({
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'mobile': '0123456789',
        }, user=system_controller)
        assert not form.is_valid()

    def test_form_invalid_if_int_number_invalid(self, system_controller, settings):
        settings.SAFE_HAVEN_DOMAIN = 'example.com'
        form = CreateUserForm({
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'mobile': '+4412345678',
        }, user=system_controller)
        assert not form.is_valid()
