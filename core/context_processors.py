from django.conf import settings


def environment(request):
    return {
        # TODO : should be deprecated and replaced by a value in context view
        "is_embedded": "iframe" in request.GET or "carte" in request.GET,
        "is_iframe": "iframe" in request.GET,
        "is_carte": "carte" in request.GET,
        "AIRFLOW_WEBSERVER_REFRESHACTEUR_URL": (
            settings.AIRFLOW_WEBSERVER_REFRESHACTEUR_URL
        ),
        "ENVIRONMENT": settings.ENVIRONMENT,
        "DEBUG": settings.DEBUG,
    }
