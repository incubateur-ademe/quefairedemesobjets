from django.conf import settings
from django.http import HttpResponse

from core.views import static_file_content_from


def get_carte_iframe_script(request):
    return static_file_content_from("carte.js")


def get_formulaire_iframe_script(request):
    return static_file_content_from("iframe.js")


def google_verification(request):
    content = f"google-site-verification: {settings.LVAO.get('GOOGLE_SEARCH_CONSOLE')}"
    return HttpResponse(content, content_type="text/plain")
