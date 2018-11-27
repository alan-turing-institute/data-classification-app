from unittest.mock import Mock, patch

import pytest

from identity.pipeline import determine_role, user_fields


@pytest.fixture
def azure_backend():
    backend = Mock()
    backend.configure_mock(name='azuread-tenant-oauth2')
    return backend


@pytest.mark.django_db
class TestUserFields:
    def _set_response(self, mock_client, data={}, ok=True):
        response = mock_client.return_value.get.return_value
        response.ok = ok
        if ok:
            response.json.return_value = data

    @patch('identity.pipeline._authenticated_client')
    def test_stores_upn_as_username(self, mock_client, azure_backend, user1):
        self._set_response(mock_client, ok=False)
        response = {'upn': 'azure-username@azure-domain.com'}

        user_fields(azure_backend, user1, response)

        user1.refresh_from_db()
        assert user1.username == 'azure-username@azure-domain.com'

    def test_does_not_store_upn_if_backend_mismatch(self, user1):
        backend = Mock()
        backend.configure_mock(name='some-other-backend')

        original_username = user1.username

        user_fields(backend, user1, {})

        user1.refresh_from_db()
        assert user1.username == original_username

    @patch('identity.pipeline._authenticated_client')
    def test_stores_mail_as_email(self, mock_client, azure_backend, user1):
        oauth_response = {'upn': 'azure-username@azure-domain.com'}

        self._set_response(mock_client, {
            'mail': 'my-email@example.com'
        })

        user_fields(azure_backend, user1, oauth_response)

        user1.refresh_from_db()
        assert user1.email == 'my-email@example.com'

    @patch('identity.pipeline._authenticated_client')
    def test_detects_sys_controller(self, mock_client, azure_backend, user1):
        self._set_response(mock_client, {
            'value': [{
                'displayName': 'SG System Controllers',
            }]
        })

        determine_role(azure_backend, user1, {})

        user1.refresh_from_db()
        assert user1.role == 'system_controller'
