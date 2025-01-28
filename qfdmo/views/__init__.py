from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.cache import cache_control

from core.views import static_file_content_from


@cache_control(max_age=31536000)
def get_carte_iframe_script(request):
    return static_file_content_from("carte.js")


def google_verification(request):
    content = f"google-site-verification: {settings.QFDMO_GOOGLE_SEARCH_CONSOLE}"
    return HttpResponse(content, content_type="text/plain")
