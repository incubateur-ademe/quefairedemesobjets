from django.conf import settings
from django.urls import reverse

from qfdmd.forms import HeaderSearchForm, SearchForm

from . import constants


def environment(request):
    return {
        "ENVIRONMENT": settings.ENVIRONMENT,
        "DEBUG": settings.DEBUG,
        "STIMULUS_DEBUG": settings.STIMULUS_DEBUG,
        "POSTHOG_DEBUG": settings.POSTHOG_DEBUG,
        "BLOCK_ROBOTS": settings.BLOCK_ROBOTS,
        "is_embedded": getattr(request, "iframe", False),
        "turbo": request.headers.get("Turbo-Frame"),
        "VERSION": settings.VERSION,
        "APP": settings.APP,
    }


def content(request):
    return vars(constants)


def global_context(request) -> dict:
    base = {
        "iframe": getattr(request, "iframe", False),
        "BASE_URL": settings.BASE_URL,
        "assistant": {
            "is_home": request.path == reverse("qfdmd:home"),
            "POSTHOG_KEY": settings.ASSISTANT["POSTHOG_KEY"],
            "MATOMO_ID": settings.ASSISTANT["MATOMO_ID"],
        },
        "CARTE": {
            "DECLARATION_ACCESSIBILITE_PAGE_ID": settings.CARTE[
                "DECLARATION_ACCESSIBILITE_PAGE_ID"
            ],
            "POSTHOG_KEY": settings.CARTE["POSTHOG_KEY"],
            "MATOMO_ID": settings.CARTE["MATOMO_ID"],
            **constants.CARTE,
        },
    }

    home_search_form = SearchForm(prefix="home", initial={"id": "home"})
    header_autocomplete_search_form = HeaderSearchForm(prefix="header-autocomplete")

    return {
        **base,
        "home_search_form": home_search_form,
        "header_autocomplete_search_form": header_autocomplete_search_form,
        **constants.ASSISTANT,
    }
