from django.conf import settings
from django.urls import reverse

from . import constants


def environment(request):
    host_without_port = request.get_host().split(":")[0]
    return {
        "ENVIRONMENT": settings.ENVIRONMENT,
        "DEBUG": settings.DEBUG,
        "is_embedded": True,
        "is_ademe": host_without_port in settings.ALLOWED_HOSTS,
        "turbo": request.headers.get("Turbo-Frame"),
    }


def content(request):
    return vars(constants)


def assistant(request):
    return {
        "is_home": request.path == reverse("qfdmd:home"),
    }
