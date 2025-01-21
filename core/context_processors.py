from django.conf import settings
from django.urls import reverse

from . import constants


def environment(request):
    return {
        "ENVIRONMENT": settings.ENVIRONMENT,
        "DEBUG": settings.DEBUG,
        "STIMULUS_DEBUG": settings.STIMULUS_DEBUG,
        "POSTHOG_DEBUG": settings.POSTHOG_DEBUG,
        "is_embedded": True,
        "turbo": request.headers.get("Turbo-Frame"),
    }


def content(request):
    return vars(constants)


def assistant(request) -> dict:
    return {
        "assistant": {
            "is_iframe": "iframe" in request.GET,
            "is_home": request.path == reverse("qfdmd:home"),
            "POSTHOG_KEY": settings.ASSISTANT["POSTHOG_KEY"],
            "MATOMO_ID": settings.ASSISTANT["MATOMO_ID"],
        },
    }
