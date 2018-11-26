from django.conf import settings
from ldap3 import Connection, Server


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
    conn.bind()
    return conn


def create_user(username):
    conn = _connect_ldap()
    attrs = {
        'cn': username,
        'objectClass': settings.AD_USER_OBJECT_CLASSES,
    }
    dn = settings.AD_RESEARCH_USER_DN % dict(cn=username)
    if not conn.add(dn, attributes=attrs):
        raise Exception('Failed to create remote user')
