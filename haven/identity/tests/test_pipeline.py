from unittest.mock import Mock, patch

import pytest
from django.conf import settings

from identity.pipeline import determine_role, find_existing_user, user_fields


@pytest.fixture
def azure_backend():
    backend = Mock()
    backend.configure_mock(name='azuread-tenant-oauth2')
    return backend


@pytest.mark.django_db
class TestUserFields:
    @patch('identity.pipeline.user_client')
    def test_stores_upn_as_username(self, mock_client, azure_backend, user1):
        oauth_response = {'upn': 'azure-username@azure-domain.com'}

        mock_client.return_value.get_me.return_value.ok = False

        user_fields(azure_backend, user1, oauth_response)

        user1.refresh_from_db()
        assert user1.username == 'azure-username@azure-domain.com'

    def test_does_not_store_upn_if_backend_mismatch(self, user1):
        backend = Mock()
        backend.configure_mock(name='some-other-backend')

        original_username = user1.username

        user_fields(backend, user1, {})

        user1.refresh_from_db()
        assert user1.username == original_username

    @patch('identity.pipeline.user_client')
    def test_stores_mail_as_email(self, mock_client, azure_backend, user1):
        oauth_response = {'upn': 'azure-username@azure-domain.com'}

        response = mock_client.return_value.get_me.return_value
        response.ok = True
        response.json.return_value = {
            'mail': 'my-email@example.com'
        }

        user_fields(azure_backend, user1, oauth_response)

        user1.refresh_from_db()
        assert user1.email == 'my-email@example.com'


    @patch('identity.pipeline.user_client')
    def test_db_email_not_changed_if_return_value_empty(self, mock_client, azure_backend, user1):
        oauth_response = {'upn': 'azure-username@azure-domain.com'}

        response = mock_client.return_value.get_me.return_value
        response.ok = True
        response.json.return_value = {
            'mail': ''
        }

        user_fields(azure_backend, user1, oauth_response)

        user1.refresh_from_db()
        assert user1.email == 'user@example.com'


@pytest.mark.django_db
@patch('identity.pipeline.user_client')
class TestDetermineRole:
    def test_detects_sys_controller(self, mock_client, azure_backend, user1):
        response = mock_client.return_value.get_my_memberships.return_value
        response.ok = True
        response.json.return_value = {'value': [{
            'displayName': settings.SECURITY_GROUP_SYSTEM_MANAGERS,
        }]}

        determine_role(azure_backend, user1, {})

        user1.refresh_from_db()
        assert user1.role == 'system_manager'

    def test_detects_programme_manager(self, mock_client, azure_backend, user1):
        response = mock_client.return_value.get_my_memberships.return_value
        response.ok = True
        response.json.return_value = {'value': [{
            'displayName': settings.SECURITY_GROUP_PROGRAMME_MANAGERS,
        }]}

        determine_role(azure_backend, user1, {})

        user1.refresh_from_db()
        assert user1.role == 'programme_manager'

    def test_detects_no_role(self, mock_client, azure_backend, system_manager):
        response = mock_client.return_value.get_my_memberships.return_value
        response.ok = True
        response.json.return_value = {'value': [{
            'displayName': 'Safe Haven Research Users',
        }]}

        determine_role(azure_backend, system_manager, {})

        system_manager.refresh_from_db()
        assert system_manager.role == ''

    def test_no_role_if_error(self, mock_client, azure_backend, system_manager):
        mock_client.return_value.get_my_memberships.return_value.ok = False

        determine_role(azure_backend, system_manager, {})

        system_manager.refresh_from_db()
        assert system_manager.role == ''

    def test_programme_manager_role_not_preserved(self, mock_client, azure_backend, programme_manager):
        response = mock_client.return_value.get_my_memberships.return_value
        response.ok = True
        response.json.return_value = {'value': []}

        determine_role(azure_backend, programme_manager, {})

        programme_manager.refresh_from_db()
        assert programme_manager.role == ''

    def test_does_nothing_if_backend_mismatch(self, mock_client, system_manager):
        backend = Mock()
        backend.configure_mock(name='some-other-backend')

        determine_role(backend, system_manager, {})

        system_manager.refresh_from_db()
        assert system_manager.role == 'system_manager'


@pytest.mark.django_db
class TestFindExistingUser:
    def test_finds_matching_username(self, azure_backend, user1):
        result = find_existing_user(azure_backend, None, {
            'upn': user1.username,
        })

        assert result['user'] == user1

    def test_returns_None_if_no_match(self, azure_backend, user1):
        result = find_existing_user(azure_backend, None, {
            'upn': 'some-random-upn'
        })

        assert result is None

    def test_returns_None_if_user_in_args(self, azure_backend, user1):
        result = find_existing_user(azure_backend, user1, {
            'upn': user1.username,
        })

        assert result is None

    def test_returns_None_if_backend_mismatch(self):
        backend = Mock()
        backend.configure_mock(name='some-other-backend')

        result = find_existing_user(backend, None, {})

        assert result is None
