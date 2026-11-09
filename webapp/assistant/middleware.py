"""The assistant only lives in iframes: search engines must not see it."""

from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.urls import reverse
from django.utils.cache import patch_vary_headers

from qfdmd.models import ProduitPage


def _is_assistant(request) -> bool:
    match = getattr(request, "resolver_match", None)
    return match is not None and match.namespace == "assistant"


def _fiche_url(request, view_kwargs) -> str:
    """The site's page for the fiche of the screen, or its home page."""
    slug = view_kwargs.get("slug") or request.GET.get("fiche")
    fiche = ProduitPage.objects.live().filter(slug=slug).first() if slug else None
    return (fiche and fiche.get_url(request)) or reverse("qfdmd:home")


class IframeOnlyMiddleware:
    """Every page of the assistant is `noindex`; one opened outside an iframe
    (`Sec-Fetch-Dest: document`) redirects to the matching page of the site.

    The answer depends on `Sec-Fetch-Dest`, hence `Vary`: nginx, which caches
    redirects, already keys its cache on it.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if _is_assistant(request):
            response["X-Robots-Tag"] = "noindex, nofollow"
            patch_vary_headers(response, ["Sec-Fetch-Dest"])
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if (
            _is_assistant(request)
            and request.headers.get("Sec-Fetch-Dest") == "document"
            and settings.ASSISTANT["V2_STANDALONE_REDIRECT"]
        ):
            return HttpResponsePermanentRedirect(_fiche_url(request, view_kwargs))
        return None
