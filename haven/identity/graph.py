import logging
from urllib.parse import urljoin

from django.conf import settings
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


logger = logging.getLogger(__name__)


GRAPH_URL = 'https://graph.microsoft.com/v1.0/'
GRAPH_SCOPE = 'https://graph.microsoft.com/.default',

TOKEN_URL = 'https://login.microsoftonline.com/{}/oauth2/v2.0/token'.format(
    settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID
)


class GraphClient:
    def __init__(self, oauth2_session):
        self._session = oauth2_session

    def get_user(self, upn):
        logger.debug("Looking in AAD for user with UPN %s" % upn)
        return self._session.get(urljoin(GRAPH_URL, f'users/{upn}'))

    def get_me(self):
        logger.debug("Querying AAD for logged in user's profile")
        return self._session.get(urljoin(GRAPH_URL, 'me'))

    def get_my_memberships(self):
        logger.debug("Querying AAD for logged in user's membership")
        return self._session.get(urljoin(GRAPH_URL, 'me/memberOf'))


def application_client():
    client_id = settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY
    client_secret = settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET

    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)
    token = oauth.fetch_token(
        token_url=TOKEN_URL,
        client_id=client_id,
        client_secret=client_secret,
        scope=GRAPH_SCOPE,
    )
    return GraphClient(OAuth2Session(token=token))


def user_client(user):
    """
    Get an oauth2 session for a user

    :param user: User object
    :return: `OAuth2Session` object
    """
    token = user.social_auth.first().extra_data
    return GraphClient(OAuth2Session(token=token))
