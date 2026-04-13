from typing import Any

from django.conf import settings
from django.views.generic import FormView

from core.views import static_file_content_from
from infotri.constants import (
    CATEGORIE_SVG_TEMPLATES,
    CONSIGNE_SVG_TEMPLATES,
    PHRASE_SVG_TEMPLATES,
)
from infotri.forms import InfotriForm


def get_infotri_iframe_script(request):
    return static_file_content_from("embed/infotri.js")


def get_infotri_configurator_iframe_script(request):
    return static_file_content_from("embed/infotri-configurator.js")


class InfotriEmbedView(FormView):
    """
    Embed view that displays the actual Info-tri visual.
    This is loaded in an iframe on third-party sites.
    """

    form_class = InfotriForm
    template_name = "ui/pages/infotri_embed.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.GET:
            kwargs["data"] = self.request.GET
        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["base_url"] = settings.BASE_URL
        context["show_code"] = self.request.GET.get("show_code") == "true"
        context["categorie_svg_templates"] = CATEGORIE_SVG_TEMPLATES
        context["consigne_svg_templates"] = CONSIGNE_SVG_TEMPLATES
        context["phrase_svg_templates"] = PHRASE_SVG_TEMPLATES
        return context

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))
