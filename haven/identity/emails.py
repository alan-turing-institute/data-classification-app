from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from social_django.utils import load_strategy

from .backends import CustomAzureOAuth2Backend


def send_activation_email(user):
    """
    Send the user an email inviting them to log in
    We use the social:begin url rather than social:complete for
    the redirect URL because the completion code expects the session
    to have been set up earlier, but this is not the case since it
    will be the user's first interaction with the site.
    At that point, they'll be logged in with Azure anyway so should
    get redirected quickly through the flow to a full site login.

    :param user: User object
    """
    backend = CustomAzureOAuth2Backend(
        load_strategy(),
        redirect_uri=urljoin(
            settings.BASE_URL,
            reverse('social:begin', args=['azuread-tenant-oauth2']))
    )

    message = render_to_string(
        'identity/email/invitation.txt', {
            'auth_url': backend.auth_url(),
            'full_name': user.get_full_name(),
            'upn': user.username,
            'webapp_title': settings.WEBAPP_TITLE
        }
    )

    return send_mail(
        subject=f'Invitation to the { settings.WEBAPP_TITLE } tool',
        message=message,
        from_email=settings.DEFAULT_FROM_MAIL,
        recipient_list=[user.email]
    )
