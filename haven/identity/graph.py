import json
import logging
from urllib.parse import urljoin

from requests import RequestException
from requests_oauthlib import OAuth2Session
from social_django.utils import load_strategy


logger = logging.getLogger(__name__)


GRAPH_URL = "https://graph.microsoft.com/v1.0/"


class GraphClientException(IOError):
    """The graph API returned an error code or the call raised a RequestException"""

    pass


class GraphClient:
    def __init__(self, oauth2_session):
        self._session = oauth2_session

    def get_me(self):
        logger.debug("Querying AAD for logged in user's profile")
        return self._session.get(urljoin(GRAPH_URL, "me"))

    def get_my_memberships(self):
        logger.debug("Querying AAD for logged in user's membership")
        return self._session.get(urljoin(GRAPH_URL, "me/memberOf"))

    def get_user_list(self):
        logger.debug("Looking for AAD users")
        try:
            # Only return specified properties
            user_list = []
            next_url = "users?$select=userPrincipalName&$top=100"

            # Loop over pages of results with page size of 100
            while next_url:
                response = self._session.get(urljoin(GRAPH_URL, next_url))

                # Raise exception if an the call failed
                response.raise_for_status()

                # Parse the response
                response_json = json.loads(response.text)

                # Get the next set of users
                next_user_list = [item["userPrincipalName"] for item in response_json["value"]]
                user_list = user_list + next_user_list

                # Check if there are additional pages of users to be returned
                if "@odata.nextLink" in response_json:
                    next_url = response_json["@odata.nextLink"]
                else:
                    next_url = None

            return user_list
        except RequestException as e:
            raise GraphClientException(
                "The Graph call to get the user list failed with error: " + str(e)
            ) from e


def user_client(user):
    """
    Get an oauth2 session for a user

    :param user: User object
    :return: `OAuth2Session` object
    """

    social_auth = user.social_auth.first()

    if not social_auth:
        raise GraphClientException("The user is not logged into an identitiy provider")

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
    return user_client(user).get_user_list()
