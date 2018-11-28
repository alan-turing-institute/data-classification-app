import logging

from django.conf import settings
from ldap3 import Connection, Server


logger = logging.getLogger(__name__)


def _connect_ldap():
    server = Server(
        settings.LDAP_SERVER,
        connect_timeout=5,
    )
    conn = Connection(
        server,
        user=settings.LDAP_USER,
        password=settings.LDAP_PASSWORD,
    )
    if not conn.bind():
        message = conn.result['message']
        logger.error(message)
        raise Exception('Failed to bind connection: %s' % message)
    return conn


def create_user(user):
    cn = user.username.split('@')[0]

    conn = _connect_ldap()
    attrs = {
        'cn': cn,
        'samAccountName': cn,
        'givenName': user.first_name,
        'sn': user.last_name,
        'mail': user.email,
        'userPrincipalName': user.username,
        'displayName': user.get_full_name(),
        'objectClass': settings.AD_USER_OBJECT_CLASSES,
    }
    dn = settings.AD_RESEARCH_USER_DN % dict(cn=cn)
    if conn.add(dn, attributes=attrs):
        user.set_aad_status(user.AAD_STATUS_PENDING)
    else:
        user.set_aad_status(user.AAD_STATUS_FAILED_TO_CREATE)
        message = conn.result['message']
        logger.error(message)
        raise Exception('Failed to create remote user: %s' % message)
