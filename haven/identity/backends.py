from django.conf import settings
from social_core.backends.azuread_tenant import AzureADTenantOAuth2


class CustomAzureOAuth2Backend(AzureADTenantOAuth2):
    def get_user_details(self, response):
        """Return user details from Azure AD account"""
        # Overrides the default backend implementation because
        # we want the UPN to be the username, not the user's full name.
        fullname, first_name, last_name = (
            response.get('name', ''),
            response.get('given_name', ''),
            response.get('family_name', '')
        )
        return {'username': response.get('upn'),
                'email': response.get('mail'),
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def auth_extra_arguments(self):
        """Return extra arguments needed on auth process."""
        extra_arguments = super(AzureADTenantOAuth2, self).auth_extra_arguments()

        # Adds an extra parameter prompt=select_account to the request.
        # This allows the user to select which account to sign in with, or to
        # add an account instead of automatically signing in with the last
        # account. This is important for preventing automatic signin with the
        # wrong account.
        extra_arguments.update({'prompt': 'select_account'})

        # Adds an extra parameter domain_hint which filters the list of
        # accounts the user selects from when they have multuple Microsoft
        # accounts
        extra_arguments.update({'domain_hint': settings.SAFE_HAVEN_DOMAIN})
        return extra_arguments
