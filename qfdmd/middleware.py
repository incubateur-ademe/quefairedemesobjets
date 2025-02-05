class AssistantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        self._set_logged_in_cookie(request, response)
        self._handle_iframe_cookie(request, response)
        self._cleanup_vary_header(response)

        return response

    def _set_logged_in_cookie(self, request, response):
        """Set or update the 'logged-in' header based on authentication."""
        cookie_name = "logged_in"
        if hasattr(request, "user") and request.user.is_authenticated:
            response.set_cookie(cookie_name, "1")
        elif request.COOKIES.get(cookie_name):
            response.delete_cookie(cookie_name)

    def _handle_iframe_cookie(self, request, response):
        """Manage iframe-related headers and cookies."""
        iframe_in_request = "iframe" in request.GET
        iframe_cookie = response.cookies.get("iframe")

        if iframe_in_request:
            response.set_cookie("iframe", "1")
            response.headers["iframe"] = "1"
        elif iframe_cookie and iframe_cookie.value == "1":
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
