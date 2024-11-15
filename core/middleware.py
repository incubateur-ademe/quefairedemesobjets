from django.conf import settings
from django.shortcuts import redirect

REDIRECTION_URL = "https://longuevieauxobjets.ademe.fr/lacarte/"


class CarteRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            "carte" not in request.GET
            and "iframe" not in request.GET
            and not settings.DEBUG
        ):
            return redirect(REDIRECTION_URL)

        response = self.get_response(request)
        return response
