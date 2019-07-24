from django.contrib.auth import BACKEND_SESSION_KEY
from django.urls import reverse


def login_backends(request):
    supported_backends = (
        {'id': 'identity.backends.CustomAzureOAUth2Backend', 'name': 'Azure', 'url': reverse('social:begin', args=['azuread-tenant-oauth2'])},
        {'id': 'django.contrib.auth.backends.ModelBackend', 'name': 'Local', 'url': reverse('admin:login') + '?next=' + request.path},
    )
    default_backend = None
    if len(supported_backends) == 1:
        default_backend = supported_backends[0]
    else:
        saved_backend = request.session.get(BACKEND_SESSION_KEY)
        if saved_backend:
            for b in supported_backends:
                if b['id'] == saved_backend:
                    default_backend = b
                    break

    return {
        'default_login_backend': default_backend,
        'supported_login_backends': supported_backends,
    }
