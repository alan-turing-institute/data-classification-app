from unittest.mock import Mock, patch

import pytest

from identity.pipeline import user_fields


@pytest.mark.django_db
class TestUserFields:
    @patch('identity.pipeline._authenticated_client')
    def test_stores_upn_as_username(self, mock_client, user1):
        backend = Mock()
        backend.configure_mock(name='azuread-tenant-oauth2')

        mock_client.return_value.get.return_value.ok = False
        response = {'upn': 'azure-username@azure-domain.com'}

        user_fields(backend, user1, response)

        user1.refresh_from_db()
        assert user1.username == 'azure-username@azure-domain.com'

    def test_does_not_store_upn_if_backend_mismatch(self, user1):
        backend = Mock()
        backend.configure_mock(name='some-other-backend')
        response = {}
        original_username = user1.username

        user_fields(backend, user1, response)

        user1.refresh_from_db()
        assert user1.username == original_username

    @patch('identity.pipeline._authenticated_client')
    def test_stores_mail_as_email(self, mock_client, user1):
        backend = Mock()
        backend.configure_mock(name='azuread-tenant-oauth2')

        mock_client.return_value.get.return_value.ok = True
        mock_client.return_value.get.return_value.json.return_value = {
            'mail': 'my-email@example.com'
        }
        response = {'upn': 'azure-username@azure-domain.com'}

        user_fields(backend, user1, response)

        user1.refresh_from_db()
        assert user1.email == 'my-email@example.com'
