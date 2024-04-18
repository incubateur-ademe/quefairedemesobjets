from django.conf import settings


def environment(request):
    return {"ENVIRONMENT": settings.ENVIRONMENT}
