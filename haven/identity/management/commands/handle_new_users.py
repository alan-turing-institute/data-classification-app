import logging

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

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
                user.set_aad_status(user.AAD_STATUS_CREATED)

                # Send the user an email inviting them to log in
                message = render_to_string(
                    'identity/email/invitation.txt', {
                        'tenant_id': tenant_id,
                        'full_name': user.get_full_name(),
                        'upn': upn,
                    }
                )
                result = send_mail(
                    subject='Invitation to data safe haven',
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
