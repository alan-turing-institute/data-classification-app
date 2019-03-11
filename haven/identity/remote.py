import logging

from django.conf import settings
from ldap3 import Connection, Server


logger = logging.getLogger(__name__)


def _connect_ldap():
    """
    Connect and bind to LDAP server as configured in settings

    :return: `ldap3.Connection` object if conneciton was successful
    :raise: Exception on failure to bind
    """
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
    """
    Create remote version of user over LDAP

    :param user: User object
    :raise: Exception on failure to create
    """
    cn = user.username.split('@')[0]

    # https://support.microsoft.com/en-gb/help/305144/how-to-use-the-useraccountcontrol-flags-to-manipulate-user-account-pro
    DONT_EXPIRE_PASSWORD = 0x10000
    NORMAL_USER_ACCOUNT = 0x0200
    PASSWORD_NOT_REQUIRED = 0x0020

    # http://kirste.userpage.fu-berlin.de/diverse/doc/ISO_3166.html for country codes
    COUNTRY_CODE_UK = 826
    conn = _connect_ldap()
    attrs = {
        'cn': cn,
        'samAccountName': cn,
        'givenName': user.first_name,
        'sn': user.last_name,
        'displayName': user.get_full_name(),
        'mail': user.email,
        'userPrincipalName': user.username,
        'mobile': str(user.mobile),
        'countryCode': COUNTRY_CODE_UK,
        'userAccountControl': DONT_EXPIRE_PASSWORD | NORMAL_USER_ACCOUNT | PASSWORD_NOT_REQUIRED,
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
