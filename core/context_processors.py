from django.conf import settings
from django.urls import reverse

from . import constants


def environment(request):
    return {
        "ENVIRONMENT": settings.ENVIRONMENT,
        "DEBUG": settings.DEBUG,
        "is_embedded": True,
        "turbo": request.headers.get("Turbo-Frame"),
    }


def content(request):
    return vars(constants)


def assistant(request):
    return {
        "is_home": request.path == reverse("qfdmd:home"),
    }
