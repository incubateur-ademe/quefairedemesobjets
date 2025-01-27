import logging

logger = logging.getLogger(__name__)


class RemoveCookieFromVaryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            response.headers["logged-in"] = 1
        else:
            del response.headers["Vary"]
            response.headers["Vary"] = "iframe, logged-in"

        if "iframe" in request.GET:
            response.set_cookie("iframe", 1)

        if (
            response.cookies.get("iframe") == "1"
            or request.COOKIES.get("iframe") == "1"
        ):
            response.headers["iframe"] = 1

        return response
