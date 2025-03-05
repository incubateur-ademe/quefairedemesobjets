from django.conf import settings
from django.urls import reverse

from . import constants


def environment(request):
    return {
        "ENVIRONMENT": settings.ENVIRONMENT,
        "DEBUG": settings.DEBUG,
        "STIMULUS_DEBUG": settings.STIMULUS_DEBUG,
        "POSTHOG_DEBUG": settings.POSTHOG_DEBUG,
        "BLOCK_ROBOTS": settings.BLOCK_ROBOTS,
        "is_embedded": True,
        "turbo": request.headers.get("Turbo-Frame"),
    }


def content(request):
    return vars(constants)


def assistant(request) -> dict:
    return {
        "assistant": {
            "is_home": request.path == reverse("home"),
            "is_iframe": request.COOKIES.get("iframe") == "1"
            or "iframe" in request.GET,
            "POSTHOG_KEY": settings.ASSISTANT["POSTHOG_KEY"],
            "MATOMO_ID": settings.ASSISTANT["MATOMO_ID"],
        },
        **constants.ASSISTANT,
    }
