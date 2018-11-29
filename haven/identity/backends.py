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
