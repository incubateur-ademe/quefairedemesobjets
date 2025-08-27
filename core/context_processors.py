from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse

from core.templatetags.seo_tags import get_sharer_content
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
        "iframe": getattr(request, "iframe", False),
        "BASE_URL": settings.BASE_URL,
        "assistant": {
            "is_home": request.path == reverse("qfdmd:home"),
            "POSTHOG_KEY": settings.ASSISTANT["POSTHOG_KEY"],
            "MATOMO_ID": settings.ASSISTANT["MATOMO_ID"],
        },
        "lvao": {
            "POSTHOG_KEY": settings.LVAO["POSTHOG_KEY"],
        },
    }

    search_form = SearchForm(prefix="header", initial={"id": "header"})
    home_search_form = SearchForm(prefix="home", initial={"id": "home"})

    return {
        **base,
        "search_form": search_form,
        "home_search_form": home_search_form,
        **constants.ASSISTANT,
    }


def jinja2_globals(request):
    """Context processor to replace jinja2 global variables"""
    return {
        "static": static,
        "sharer": get_sharer_content,
        "AIRFLOW_WEBSERVER_REFRESHACTEUR_URL": getattr(
            settings, "AIRFLOW_WEBSERVER_REFRESHACTEUR_URL", ""
        ),
    }
