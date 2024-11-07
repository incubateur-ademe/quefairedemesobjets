from django.conf import settings


def environment(request):
    return {
        "ENVIRONMENT": settings.ENVIRONMENT,
        "DEBUG": settings.DEBUG,
        # Even if this variable is mainly used when navigating on the Carte
        # or Formulaire views, it is used in templates as JSON and parsed to
        # be passed to Posthog analytics.
        # It is then required to be added on every view by default, because
        # the JSON parsing might raise an exception if the variable is undefined.
        "is_embedded": "carte" in request.GET or "iframe" in request.GET,
    }
