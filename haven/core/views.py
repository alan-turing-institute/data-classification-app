from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponseRedirect

SIGNOUT_URL = 'https://login.microsoftonline.com/{}/oauth2/logout?post_logout_redirect_uri={}'


def logout(request):
    """Log out of application and out of social auth account"""
    auth_logout(request)
    url = SIGNOUT_URL.format(settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID, settings.BASE_URL)
    return HttpResponseRedirect(url)
