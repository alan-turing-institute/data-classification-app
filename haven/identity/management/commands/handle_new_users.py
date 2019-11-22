import logging

from django.core.management.base import BaseCommand

from haven.identity.emails import send_activation_email
from haven.identity.graph import application_client
from haven.identity.models import User


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check AAD for newly created users'

    def handle(self, *args, **options):
        client = application_client()

        pending = User.objects.filter(aad_status=User.AAD_STATUS_PENDING)
        for user in pending:
            response = client.get_user(user.username)
            if response.ok:
                logger.debug("User found")

                result = send_activation_email(user)

                if result:
                    logger.debug('1 mail sent')
                else:
                    logger.debug('mail failed to send')
            else:
                logger.debug("User not found")
