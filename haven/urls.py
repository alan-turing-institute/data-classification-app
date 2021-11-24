"""haven URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.urls import include, path
from django.views.generic import TemplateView
from two_factor.urls import urlpatterns as tf_urls

from haven.core import views as core_views

# uncomment to enforce mfa on the admin site

#from django.contrib import admin
#from django_otp.admin import OTPAdminSite
#admin.site.__class__ = OTPAdminSite


urlpatterns = [

    path("users/", include("haven.identity.urls", namespace="identity")),
    path("projects/", include("haven.projects.urls", namespace="projects")),
 
    path("logout/", core_views.logout, name="logout"),
    #mfa auth
    path('', include(tf_urls, namespace="two_factor")),
   
    # Externally-driven single sign out
    path("ssologout/", core_views.sso_logout, name="sso_logout"),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("auth/", include("social_django.urls", namespace="social")),
    path("error/", TemplateView.as_view(template_name="error.html"), name="error-page"),
]


handler404 = "haven.core.views.handler404"
handler500 = "haven.core.views.handler500"

# These features are only enabled for local testing
if settings.DEBUG:
    # Enable debug toolbar
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls)),] + urlpatterns

    # Enable admin interface
    from django.contrib import admin

    urlpatterns = [path("admin/", admin.site.urls),] + urlpatterns

    # Enable local user login
    from django.contrib.auth import views as auth_views

    # urlpatterns = [
    #       path(
    #          "accounts/login/",
    #          auth_views.LoginView.as_view(template_name="accounts/two_factor/core/login.html"),
    #           name="login",
    #       )
    # ] + urlpatterns


    urlpatterns = [
        path(
            "accounts/login/",
            auth_views.LoginView.as_view(template_name="identity/login.html"),
            name="login",
        )
    ] + urlpatterns

    