from unittest.mock import patch

import pytest

from identity.models import User
from identity.remote import _connect_ldap, create_user


@patch('identity.remote.Server')
@patch('identity.remote.Connection')
class TestConnectLDAP:
    def test_uses_correct_settings(self, mockConnection, mockServer, settings):
        settings.LDAP_SERVER = 'my-ldap-server'
        settings.LDAP_USER = 'ldap-user'
        settings.LDAP_PASSWORD = 'ldap-pass'

        _connect_ldap()

        mockServer.assert_called_with('my-ldap-server', connect_timeout=5)
        mockConnection.assert_called_with(
            mockServer.return_value,
            user='ldap-user',
            password='ldap-pass'
        )

    def test_returns_connection_if_bind_succeeds(self, mockConnection, mockServer):
        mock_conn = mockConnection.return_value
        mock_conn.bind.return_value = True

        assert _connect_ldap() == mock_conn

    def test_raises_exception_if_bind_fails(self, mockConnection, mockServer):
        mockConnection.return_value.bind.return_value = False

        with pytest.raises(Exception):
            _connect_ldap()


@patch('identity.remote._connect_ldap')
@pytest.mark.django_db
class TestCreateUser:
    def test_sets_status_to_pending(self, mock_conn, user1):
        mock_conn.return_value.add.return_value = True

        create_user(user1)

        user1.refresh_from_db()
        assert user1.aad_status == 'pending'

    def test_sets_status_to_failed_on_ldap_failure(self, mock_conn, user1):
        mock_conn.return_value.add.return_value = False

        with pytest.raises(Exception):
            create_user(user1)

        user1.refresh_from_db()
        assert user1.aad_status == 'failed_to_create'

    def test_calls_with_correct_dn(self, mock_conn):
        user = User.objects.create_user(
            username='user@dsg.example.com',
            email='user@example.com',
            first_name='Test',
            last_name='User',
            mobile='+443338888888',
            password='whatever',
        )

        mock_add = mock_conn.return_value.add

        create_user(user)

        mock_add.assert_called_with(
            'CN=user,OU=Safe Haven Research Users,DC=dsgroupdev,DC=co,DC=uk',
            attributes={
                'cn': 'user',
                'samAccountName': 'user',
                'givenName': 'Test',
                'sn': 'User',
                'displayName': 'Test User',
                'mail': 'user@example.com',
                'userPrincipalName': 'user@dsg.example.com',
                'mobile': '+443338888888',
                'countryCode': 826,
                'userAccountControl': 0x10220,
                'objectClass': ['user', 'organizationalPerson', 'person', 'top'],
            }
        )
