from django.conf import settings


def environment(request):
    return {
        "ENVIRONMENT": settings.ENVIRONMENT,
        "DEBUG": settings.DEBUG,
        "is_embedded": "carte" in request.GET or "iframe" in request.GET,
    }
