from .common import BASE_DOMAIN, MIDDLEWARE

MIDDLEWARE.append("haven.identity.auth.middleware.HttpRemoteUserMiddleware")

AUTHENTICATION_BACKENDS = [
    'haven.identiry.auth.backends.RemoteExtendedUserBackend',
]

# Logout from authelia after logout from Django app
LOGOUT_REDIRECT_URL = "https://auth." + BASE_DOMAIN + "/logout"