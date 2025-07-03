class AssistantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Prepare request
        self._prepare_request_if_iframe(request)
        response = self.get_response(request)

        # Prepare response
        self._set_logged_in_cookie(request, response)
        self._persist_iframe_in_headers(request, response)
        self._cleanup_vary_header(response)

        return response

    def _set_logged_in_cookie(self, request, response):
        """Set or update the 'logged-in' header based on authentication.
        It is use to bypass cache by nginx.

        If present, the logged_in cookie bypasses the cache."""
        cookie_name = "logged_in"

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
