from django.conf import settings
from django.urls import reverse

from qfdmd.forms import SearchForm

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
        "VERSION": settings.VERSION,
        "APP": settings.APP,
    }


def content(request):
    return vars(constants)


def global_context(request) -> dict:
    base = {
        "assistant": {
            "is_home": request.path == reverse("home"),
            "is_iframe": request.COOKIES.get("iframe") == "1"
            or "iframe" in request.GET,
            "POSTHOG_KEY": settings.ASSISTANT["POSTHOG_KEY"],
            "MATOMO_ID": settings.ASSISTANT["MATOMO_ID"],
            "BASE_URL": settings.ASSISTANT["BASE_URL"],
        },
        "lvao": {"BASE_URL": settings.LVAO["BASE_URL"]},
    }

    if request.META.get("HTTP_HOST") not in settings.ASSISTANT["HOSTS"]:
        return base

    return {
        **base,
        "search_form": SearchForm(),
        **constants.ASSISTANT,
    }
