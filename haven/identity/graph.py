import logging
from urllib.parse import urljoin

from django.conf import settings
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


logger = logging.getLogger(__name__)


GRAPH_URL = 'https://graph.microsoft.com/v1.0/'


class GraphClient:
    def __init__(self, oauth2_session):
        self._session = oauth2_session

    def get_me(self):
        logger.debug("Querying AAD for logged in user's profile")
        return self._session.get(urljoin(GRAPH_URL, 'me'))

    def get_my_memberships(self):
        logger.debug("Querying AAD for logged in user's membership")
        return self._session.get(urljoin(GRAPH_URL, 'me/memberOf'))


def user_client(user):
    """
    Get an oauth2 session for a user

    :param user: User object
    :return: `OAuth2Session` object
    """
    token = user.social_auth.first().extra_data
    return GraphClient(OAuth2Session(token=token))
