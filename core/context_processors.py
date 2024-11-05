from django.conf import settings


def environment(request):
    return {
        "ENVIRONMENT": settings.ENVIRONMENT,
        "DEBUG": settings.DEBUG,
        "is_embedded": "carte" in request.GET or "iframe" in request.GET,
        "is_carte": "carte" in request.GET,  # TODO: Voir pour gérer ca autrement,
        # je m'en sers pour déclencher la couleur dans les tags de la barre latérale
    }
