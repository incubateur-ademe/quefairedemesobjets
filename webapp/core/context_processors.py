from django.conf import settings
from django.core.cache import cache
from django.urls import reverse

from qfdmd.forms import (
    DEFAULT_HEADER_SEARCH_PLACEHOLDER,
    DEFAULT_HOME_SEARCH_PLACEHOLDER,
    QfSearchForm,
)

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


def _get_search_placeholders():
    cache_key = "search_settings_placeholders"
    value = cache.get(cache_key)
    if value is not None:
        return value

    try:
        from qfdmd.models import SearchSettings

        settings_obj = SearchSettings.load()
        placeholders = (
            settings_obj.search_placeholder or DEFAULT_HOME_SEARCH_PLACEHOLDER,
            settings_obj.header_search_placeholder or DEFAULT_HEADER_SEARCH_PLACEHOLDER,
        )
    except Exception:
        placeholders = (
            DEFAULT_HOME_SEARCH_PLACEHOLDER,
            DEFAULT_HEADER_SEARCH_PLACEHOLDER,
        )

    cache.set(cache_key, placeholders, timeout=3600)
    return placeholders


def global_context(request) -> dict:
    (
        home_placeholder,
        header_placeholder,
    ) = _get_search_placeholders()
    header_search_form = QfSearchForm(prefix="header-autocomplete")
    header_search_form.fields["search"].widget.attrs["placeholder"] = header_placeholder
    homepage_search_form = QfSearchForm(prefix="home")
    homepage_search_form.fields["search"].widget.attrs["placeholder"] = home_placeholder
    skiplinks = [
        {"link": "#content", "label": "Contenu"},
    ]

    return {
        "iframe": getattr(request, "iframe", False),
        "BASE_URL": settings.BASE_URL,
        "assistant": {
            "is_home": request.path == reverse("qfdmd:home"),
            "POSTHOG_KEY": settings.ASSISTANT["POSTHOG_KEY"],
            "MATOMO_ID": settings.ASSISTANT["MATOMO_ID"],
            "header_search_form": header_search_form,
            "homepage_search_form": homepage_search_form,
        },
        "CARTE": {
            "DECLARATION_ACCESSIBILITE_PAGE_ID": settings.CARTE[
                "DECLARATION_ACCESSIBILITE_PAGE_ID"
            ],
            "MATOMO_ID": settings.CARTE["MATOMO_ID"],
            **constants.CARTE,
        },
        "skiplinks": skiplinks,
        **constants.ASSISTANT,
    }
