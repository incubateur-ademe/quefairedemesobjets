import logging
from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve
from wagtail.admin.viewsets.base import reverse

from core.utils import has_explicit_perm

logger = logging.getLogger(__name__)


class BetaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def _set_beta_mode_from(self, request):
        request.beta = False
        if request.user.is_authenticated:
            request.beta = has_explicit_perm(
                request.user, "wagtailadmin.can_see_beta_search"
            )

    def __call__(self, request):
        self._set_beta_mode_from(request)
        response = self.get_response(request)
        return response


class RequestEnhancementMiddleware:
    LOGGED_IN_COOKIE = "logged_in"
    CMS_CARTE_FALLBACK = "/lacarte"
    CARTE_PARAM = "carte"
    IFRAME_PARAM = "iframe"
    FORMULAIRE_PARAM = "formulaire"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Prepare request
        if url_to_redirect := self._check_redirect_from_legacy_domains(request):
            return redirect(url_to_redirect, permanent=True)

        self._prepare_request_if_iframe(request)
        response = self.get_response(request)

        # Prepare response
        self._set_logged_in_cookie(request, response)
        self._persist_iframe_in_headers(request, response)
        self._cleanup_vary_header(response)

        return response

    def _check_redirect_from_legacy_domains(self, request) -> str | None:
        """
        Handle direct access routing for legacy paths
        based on host and query parameters.

        Routes requests to:
        - Carte view when 'carte' parameter present (highest priority)
        - Formulaire view when 'iframe' parameter present
        - Main domain redirect for allowed hosts
        - CMS carte page as fallback for unknown hosts
        """
        # Check for special query parameters first (highest priority)
        if redirect_url := self._handle_special_query_params(request):
            return redirect_url

        # Handle host-based redirects
        # TODO: handle in nginx as well
        # return self._handle_host_redirects(request)
        return None

    def _handle_special_query_params(self, request) -> str | None:
        if resolve(request.path).view_name != "qfdmd:home":
            return

        if self.CARTE_PARAM in request.GET:
            return self._build_redirect_url(
                "qfdmo:carte", request.GET, [self.CARTE_PARAM]
            )

        if self.IFRAME_PARAM in request.GET or self.FORMULAIRE_PARAM in request.GET:
            return self._build_redirect_url(
                "qfdmo:formulaire",
                request.GET,
                [self.IFRAME_PARAM, self.FORMULAIRE_PARAM],
            )
        return None

    def _build_redirect_url(
        self,
        view_name: str,
        get_params,
        params_to_remove: list,
    ) -> str:
        from urllib.parse import urljoin

        get_params_copy = get_params.copy()

        for param in params_to_remove:
            get_params_copy.pop(param, None)  # Use pop() to avoid KeyError

        query_string = get_params_copy.urlencode()
        relative_url = reverse(view_name)

        base_url = settings.BASE_URL.rstrip("/")
        absolute_url = urljoin(base_url, relative_url.lstrip("/"))
        return f"{absolute_url}?{query_string}" if query_string else absolute_url

    def _handle_host_redirects(self, request) -> str | None:
        base_netloc = urlparse(settings.BASE_URL).netloc
        base_scheme = urlparse(settings.BASE_URL).scheme
        request_host = request.META.get("HTTP_HOST")

        if not request_host or request_host == base_netloc:
            return None

        if request_host in settings.ALLOWED_HOSTS:
            # Redirect to main domain while preserving path and query params
            full_requested_url = urlparse(request.build_absolute_uri())
            redirect_url = urlunparse(
                full_requested_url._replace(netloc=base_netloc, scheme=base_scheme)
            )
            logger.info(
                f"Redirecting {full_requested_url.path} "
                f"from {request_host} to {base_netloc}"
            )
            return redirect_url

        # Unknown host - redirect to CMS
        logger.info(f"Unknown host {request_host} redirected to CMS carte page")
        return f"{settings.CMS['BASE_URL']}{self.CMS_CARTE_FALLBACK}"

    def _set_logged_in_cookie(self, request, response):
        """Set or update the 'logged-in' header based on authentication.
        It is use to bypass cache by nginx.

        If present, the logged_in cookie bypasses the cache."""
        cookie_name = self.LOGGED_IN_COOKIE

        # In some cases, gunicorn can be reached directly without going through
        # nginx, when reaching http://localhost:8000 directly for example, that
        # triggers a DisallowedHost error as localhost is not in
        # settings.ALLOWED_HOSTS.
        # This causes user to not be defined on request object and raises an
        # AttributeError hiding the underlying DisallowedHost error.
        if hasattr(request, "user") and request.user.is_authenticated:
            response.set_cookie(cookie_name, "1")
        elif request.COOKIES.get(cookie_name):
            response.delete_cookie(cookie_name)

    def _prepare_request_if_iframe(self, request):
        """Detect if the request comes from an iframe.
        Detection is based on the Sec-Fetch-Dest header, which is set by modern
        browsers when a request is made from within an iframe.
        """
        request.iframe = request.headers.get("Sec-Fetch-Dest") == "iframe"

    def _persist_iframe_in_headers(self, request, response):
        """Persist iframe state in headers.
        This is useful as headers are used as a cache key with nginx.
        iFrame version of pages are cached differently."""

        if request.iframe:
            response.headers["iframe"] = "1"
        else:
            # Ensure the iframe header is not lingering
            response.headers.pop("iframe", None)

    @staticmethod
    def _cleanup_vary_header(response):
        """Helper to parse and return the Vary header as a list."""
        vary_header = response.headers.get("Vary", "")
        return [
            v.strip()
            for v in vary_header.split(",")
            if v.strip() and v.strip().lower() != "cookie"
        ]
