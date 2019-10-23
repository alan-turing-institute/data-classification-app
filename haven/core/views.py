from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic import TemplateView
from sourcerevision.loader import get_revision

SIGNOUT_URL = 'https://login.microsoftonline.com/{}/oauth2/logout?post_logout_redirect_uri={}'


def logout(request):
    """Log out of application and out of social auth account"""
    auth_logout(request)
    url = SIGNOUT_URL.format(settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID, settings.BASE_URL)
    return HttpResponseRedirect(url)


def sso_logout(request):
    """Log out of application in response to single sign out from the auth provider"""
    auth_logout(request)
    return HttpResponse(status=200)


class HomeView(TemplateView):
    """Home page"""
    template_name = "home.html"

    @staticmethod
    def version():
        """Get the VCS build number"""

        try:
            # Try to get the hash from sourcerevision
            version_text = get_revision()
            if version_text:
                return version_text

            # If the above failed we may be a deployed Azure instance without
            # access to the git command. Try to get the kudu dpeloy hash
            deployed_version_file = '/home/site/deployments/active'
            with open(deployed_version_file) as fh:
                version_text = fh.readline()
                return version_text[:7]

        # Otherwise return Unknown
        except:
            return "Unknown"
