from django.conf import settings
from django.http import HttpResponse

from core.views import static_file_content_from


def get_carte_iframe_script(request):
    return static_file_content_from("embed/carte.js")


def get_formulaire_iframe_script(request):
    return static_file_content_from("embed/formulaire.js")


def google_verification(request):
    content = f"google-site-verification: {settings.CARTE.get('GOOGLE_SEARCH_CONSOLE')}"
    return HttpResponse(content, content_type="text/plain")
