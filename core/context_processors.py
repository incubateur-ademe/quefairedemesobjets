from django.conf import settings
from django.urls import reverse

from qfdmd.forms import SearchForm
from qfdmd.models import CMSPage
from qfdmd.views import SEARCH_VIEW_TEMPLATE_NAME, generate_iframe_script

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
        "lvao": {"BASE_URL": settings.ASSISTANT["BASE_URL"]},
    }

    if request.META.get("HTTP_HOST") not in settings.ASSISTANT["HOSTS"]:
        return base

    return {
        **base,
        "footer_pages": CMSPage.objects.all(),
        "search_form": SearchForm(),
        "search_view_template_name": SEARCH_VIEW_TEMPLATE_NAME,
        "iframe_script": generate_iframe_script(request),
        **constants.ASSISTANT,
    }
