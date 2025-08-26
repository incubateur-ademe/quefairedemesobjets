import logging
from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.shortcuts import redirect
from wagtail.admin.viewsets.base import reverse

logger = logging.getLogger(__name__)


class AssistantMiddleware:
    LOGGED_IN_COOKIE = "logged_in"
    CMS_CARTE_FALLBACK = "/lacarte"
    CARTE_PARAM = "carte"
    IFRAME_PARAM = "iframe"

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
        return self._handle_host_redirects(request)

    def _handle_special_query_params(self, request) -> str | None:
        get_params = request.GET.copy()

        # Order matters: 'carte' takes precedence over 'iframe'
        if self.CARTE_PARAM in get_params:
            return self._build_redirect_url(
                "qfdmo:carte", get_params, [self.CARTE_PARAM, self.IFRAME_PARAM]
            )

        if self.IFRAME_PARAM in get_params:
            return self._build_redirect_url(
                "qfdmo:formulaire", get_params, [self.IFRAME_PARAM]
            )

        return None

    def _build_redirect_url(
        self, view_name: str, get_params, params_to_remove: list
    ) -> str:
        for param in params_to_remove:
            get_params.pop(param, None)  # Use pop() to avoid KeyError

        query_string = get_params.urlencode()
        base_url = reverse(view_name)

        return f"{base_url}?{query_string}" if query_string else base_url

    def _handle_host_redirects(self, request) -> str | None:
        base_host = urlparse(settings.BASE_URL).hostname
        base_scheme = urlparse(settings.BASE_URL).scheme
        request_host = request.META.get("HTTP_HOST")

        if not request_host or request_host == base_host:
            return None

        if request_host in settings.ALLOWED_HOSTS:
            # Redirect to main domain while preserving path and query params
            full_requested_url = urlparse(request.build_absolute_uri())
            redirect_url = urlunparse(
                full_requested_url._replace(netloc=base_host, scheme=base_scheme)
            )
            logger.info(
                f"Redirecting {full_requested_url.path} "
                f"from {request_host} to {base_host}"
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
        """Detect if the request comes from an iframe mode.
        The iframe mode is usually set on the initial request, and must be passed
        during the navigation.
        To be RGPD-compliant, and to satisfy some of our users constraints, we
        cannot use Django session's cookie.
        We rely on a mix between querystring and referrer.

        We also have a client-side fallback, based on sessionStorage : on initial
        request, we set the iframe value in sessionStorage.
        """
        is_in_iframe_mode = False
        if request.headers.get("Sec-Fetch-Dest") == "iframe":
            is_in_iframe_mode = True

        if self.IFRAME_PARAM in request.GET:
            is_in_iframe_mode = True

        request.iframe = is_in_iframe_mode

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
