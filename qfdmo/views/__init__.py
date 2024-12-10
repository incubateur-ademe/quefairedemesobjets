from django.conf import settings
from django.http import HttpResponse


def google_verification(request):
    content = f"google-site-verification: {settings.QFDMO_GOOGLE_SEARCH_CONSOLE}"
    return HttpResponse(content, content_type="text/plain")
