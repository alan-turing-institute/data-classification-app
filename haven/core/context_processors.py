from django.conf import settings

def auth_types(request):
    return {
        "AUTH_TYPES": settings.HAVEN_AUTH_TYPES,
    }