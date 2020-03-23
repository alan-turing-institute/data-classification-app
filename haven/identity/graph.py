import logging
from urllib.parse import urljoin

from django.conf import settings
from oauthlib.oauth2 import BackendApplicationClient
from requests import RequestException
from requests_oauthlib import OAuth2Session
from social_django.utils import load_strategy
import json

logger = logging.getLogger(__name__)


GRAPH_URL = 'https://graph.microsoft.com/v1.0/'


class GraphClientException(IOError):
    """The graph API returned an error code or the call raised a RequestException"""
    pass


class GraphClient:
    def __init__(self, oauth2_session):
        self._session = oauth2_session

    def get_me(self):
        logger.debug("Querying AAD for logged in user's profile")
        return self._session.get(urljoin(GRAPH_URL, 'me'))

    def get_my_memberships(self):
        logger.debug("Querying AAD for logged in user's membership")
        return self._session.get(urljoin(GRAPH_URL, 'me/memberOf'))

    def get_user_list(self):
        logger.debug("Looking for AAD users")
        try:
            response = self._session.get(urljoin(GRAPH_URL, f'users'))
            response.raise_for_status()
            return response
        except RequestException as e:
            raise GraphClientException('The Graph call to get the user list failed with error: '
                                       + str(e)) from e


def user_client(user):
    """
    Get an oauth2 session for a user

    :param user: User object
    :return: `OAuth2Session` object
    """

    social_auth = user.social_auth.first()

    if not social_auth:
        raise GraphClientException('The user is not logged into an identitiy provider')

    # load_strategy() will force a token refresh if required
    social_auth.get_access_token(load_strategy())

    token = social_auth.extra_data
    return GraphClient(OAuth2Session(token=token))


def get_system_user_list(user):
    """
    Get a list of userPrincipalNames for AD users on the SHM

    :param user: User object for authentication
    :return: List of userPrincipalNames
    """
    graph_client = user_client(user)
    names_dict = json.loads(graph_client.get_user_list().text)
    return [item['userPrincipalName'] for item in names_dict['value']]
