import logging

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from identity.context_processors import login_backends


SIGNOUT_URL = 'https://login.microsoftonline.com/{}/oauth2/logout?post_logout_redirect_uri={}'


def login(request):
    c = login_backends(request)
    if len(c['supported_login_backends']) == 1:
        return HttpResponseRedirect(c['default_login_backend']['url'])
    return render(request, 'login.html')

def logout(request):
    """Log out of application and out of social auth account"""
    backend = request.session.get(BACKEND_SESSION_KEY)
    if backend == 'identity.backends.CustomAzureOAuth2Backend':
        url = SIGNOUT_URL.format(settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID, settings.BASE_URL)
    else:
        url = settings.BASE_URL
    auth_logout(request)
    # Logging out removes this from the session, but we want to keep it to use it as a default
    # next time the user logs in
    request.session[BACKEND_SESSION_KEY] = backend
    return HttpResponseRedirect(url)


def sso_logout(request):
    """Log out of application in response to single sign out from the auth provider"""
    auth_logout(request)
    return HttpResponse(status=200)
