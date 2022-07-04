from django.contrib.auth.middleware import RemoteUserMiddleware


class HttpRemoteUserMiddleware(RemoteUserMiddleware):
    header = "HTTP_REMOTE_USER"

    # uncomment the line below to disable authentication to users that not exists on Django database
    # create_unknown_user = False
