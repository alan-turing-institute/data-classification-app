from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponseRedirect, HttpResponse

SIGNOUT_URL = 'https://login.microsoftonline.com/{}/oauth2/logout?post_logout_redirect_uri={}'


def logout(request):
    """Log out of application and out of social auth account"""

    # Get the site URL from the current request, so logout will redirect to the same domain the user is browsing
    base_url = request.build_absolute_uri('/').rstrip('/')
    auth_logout(request)
    url = SIGNOUT_URL.format(settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID, base_url)
    return HttpResponseRedirect(url)


def sso_logout(request):
    """Log out of application in response to single sign out from the auth provider"""
    auth_logout(request)
    return HttpResponse(status=200)
