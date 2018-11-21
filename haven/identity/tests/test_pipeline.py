from unittest.mock import Mock

import pytest

from identity.pipeline import user_fields


@pytest.mark.django_db
class TestUserFields:
    def test_stores_upn_as_username(self, user1):
        backend = Mock()
        backend.configure_mock(name='azuread-tenant-oauth2')
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
