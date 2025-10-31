import mimetypes

from _pytest.tmpdir import TempPathFactory
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.template import Template
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_control
from django.views.generic import ListView, TemplateView
from wagtail.templatetags.wagtailcore_tags import richtext

from qfdmd.models import EmbedSettings


def backlink(request):
    key = request.GET.get("key")
    text_content = ""
    try:
        if key == "assistant":
            text_content = EmbedSettings.objects.first().backlink_assistant
        if key == "carte":
            text_content = EmbedSettings.objects.first().backlink_carte
        if key == "formulaire":
            text_content = EmbedSettings.objects.first().backlink_formulaire
    except (AttributeError, EmbedSettings.DoesNotExist):
        pass

    response = HttpResponse(richtext(text_content), content_type="text/plain")
    response["Access-Control-Allow-Origin"] = "*"
    return response


@cache_control(max_age=31536000)
def robots_txt(request):
    text_content = render_to_string("robots.txt", request=request)
    return HttpResponse(text_content, content_type="text/plain")


def static_file_content_from(path):
    file_path = finders.find(path)

    if not file_path:
        return HttpResponse("File not found", status=404)

    content_type, _ = mimetypes.guess_type(file_path)
    # If the MIME type cannot be guessed (e.g., unknown file extension),
    # we default to application/octet-stream, which is a generic binary type.
    content_type = content_type or "application/octet-stream"

    with open(file_path, "r") as file:
        file_content = file.read()
        return HttpResponse(file_content, content_type=content_type)


class IsStaffMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class AutocompleteSousCategorieObjet(ListView):
    pass
