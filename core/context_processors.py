from django.conf import settings

from . import constants


def environment(request):
    return {
        "ENVIRONMENT": settings.ENVIRONMENT,
        "DEBUG": settings.DEBUG,
        "is_embedded": True,
    }


def content(request):
    return vars(constants)
