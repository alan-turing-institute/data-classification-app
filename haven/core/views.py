from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render


SIGNOUT_URL = (
    "https://login.microsoftonline.com/{}/oauth2/logout?post_logout_redirect_uri={}"
)


def logout(request):
    """Log out of application"""

    # Get the site URL from the current request, so logout will redirect to the same domain the user is browsing
    base_url = request.build_absolute_uri("/").rstrip("/")
    auth_logout(request)
    return HttpResponseRedirect(base_url)


def sso_logout(request):
    """Log out of application in response to single sign out from the auth provider"""
    auth_logout(request)
    return HttpResponse(status=200)


def handler404(request, exception, template_name="404.html"):
    """404 error handler"""
    return render(request, template_name, status=404)


def handler500(request):
    """500 error handler"""
    return render(request, "500.html", status=500)
