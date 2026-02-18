import mimetypes
from typing import override

import unidecode
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import TrigramWordDistance
from django.contrib.staticfiles import finders
from django.db.models.functions import Length, Lower
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_control
from django.views.generic import ListView
from wagtail.templatetags.wagtailcore_tags import richtext

from qfdmd.models import EmbedSettings, Synonyme


def backlink(request):
    key = request.GET.get("key")
    text_content = ""

    if key == "infotri-configurator":
        text_content = (
            '<a style="color: black; text-decoration: none;" '
            'href="https://quefairedemesdechets.ademe.fr/integrer-info-tri/" '
            'rel="noopener noreferrer" '
            'onMouseOver="this.style.textDecoration=`underline`"'
            'onMouseOut="this.style.textDecoration=`none`"'
            'target="_blank">configurateur proposé par quefairedemesdechets.fr</a>'
        )
    else:
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


class AutocompleteSynonyme(ListView):
    template_name = "ui/forms/widgets/autocomplete/synonyme.html"
    model = Synonyme

    @override
    def get_queryset(self):
        query = self.request.GET.get("q", "")
        limit = self.request.GET.get("limit", 10)

        if not query:
            return super().get_queryset().none()

        query = unidecode.unidecode(query)

        # TODO: use django-modelsearch
        synonymes = (
            super()
            .get_queryset()
            .annotate(
                nom_unaccent=Unaccent(Lower("nom")),
            )
            .prefetch_related("produit__sous_categories")
            .annotate(
                distance=TrigramWordDistance(query, "nom_unaccent"),
                length=Length("nom"),
            )
            .filter(produit__sous_categories__id__isnull=False)
            .order_by("distance", "length")
            .distinct()[: int(limit)]
        )

        return synonymes

    @override
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["turbo_frame_id"] = self.request.GET.get("turbo_frame_id")
        return context
