from unittest.mock import patch

import pytest

from identity.remote import create_user


@pytest.mark.django_db
class TestCreateUser:
    @patch('identity.remote._connect_ldap')
    def test_sets_status_to_pending(self, mock_conn, user1):
        mock_conn.return_value.add.return_value = True

        create_user(user1)

        user1.refresh_from_db()
        assert user1.aad_status == 'pending'

    @patch('identity.remote._connect_ldap')
    def test_sets_status_to_failed_on_ldap_failure(self, mock_conn, user1):
        mock_conn.return_value.add.return_value = False

        with pytest.raises(Exception):
            create_user(user1)

        user1.refresh_from_db()
        assert user1.aad_status == 'failed_to_create'
