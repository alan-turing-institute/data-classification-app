import logging
from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.urls import reverse
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from social_django.utils import load_strategy

from identity.backends import CustomAzureOAuth2Backend
from identity.models import User


logger = logging.getLogger(__name__)


GRAPH_URL = 'https://graph.microsoft.com/v1.0/'


class Command(BaseCommand):
    help = 'Check AAD for newly created users'

    def handle(self, *args, **options):
        client_id = settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY
        client_secret = settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET
        tenant_id = settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID

        client = BackendApplicationClient(client_id=client_id)
        oauth = OAuth2Session(client=client)
        token = oauth.fetch_token(
            token_url='https://login.microsoftonline.com/{}/oauth2/v2.0/token'.format(tenant_id),
            client_id=client_id,
            client_secret=client_secret,
            scope='https://graph.microsoft.com/.default',
        )
        client = OAuth2Session(token=token)

        pending = User.objects.filter(aad_status=User.AAD_STATUS_PENDING)
        for user in pending:
            upn = user.username
            logger.debug("Looking in AAD for user with UPN %s" % upn)
            response = client.get(GRAPH_URL + f'users/{user.username}')
            if response.ok:
                logger.debug("User found")

                # Send the user an email inviting them to log in
                # We use the social:begin url rather than social:complete for
                # the redirect URL because the completion code expects
                # the session to have been set up earlier, but this is not the
                # case since it will be the user's first interaction with the site.
                # At that point, they'll be logged in with Azure anyway so should
                # get redirected quickly through the flow to a full site login.
                backend = CustomAzureOAuth2Backend(
                    load_strategy(),
                    redirect_uri=urljoin(
                        settings.BASE_URL,
                        reverse('social:begin', args=['azuread-tenant-oauth2']))
                )

                message = render_to_string(
                    'identity/email/invitation.txt', {
                        'auth_url': backend.auth_url(),
                        'tenant_id': tenant_id,
                        'full_name': user.get_full_name(),
                        'upn': upn,
                    }
                )
                result = send_mail(
                    subject='Invitation to the Data Safe Haven',
                    message=message,
                    from_email=settings.DEFAULT_FROM_MAIL,
                    recipient_list=[user.email]

                )

                if result:
                    logger.debug('mail sent')
                else:
                    logger.debug('mail failed to send')
            else:
                logger.debug("User not found")
