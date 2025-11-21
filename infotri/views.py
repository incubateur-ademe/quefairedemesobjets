from typing import Any

from django.conf import settings
from django.views.generic import FormView, TemplateView

from core.views import static_file_content_from
from infotri.forms import InfotriForm


def get_infotri_iframe_script(request):
    return static_file_content_from("embed/infotri.js")


class InfotriConfiguratorView(FormView):
    """
    Main view for the Info-tri configurator.
    Users configure their Info-tri labels here and get the embed code.
    """

    form_class = InfotriForm
    template_name = "ui/pages/infotri.html"

    def get_form_kwargs(self):
        """Pass GET data to the form."""
        kwargs = super().get_form_kwargs()
        if self.request.GET:
            kwargs["data"] = self.request.GET
        return kwargs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["base_url"] = settings.BASE_URL

        # Get initial values from the form
        form = context.get("form")
        if form and form.is_bound and form.is_valid():
            context["initial_categorie"] = form.cleaned_data.get("categorie", "")
            context["initial_consigne"] = form.cleaned_data.get("consigne", "")
            context["initial_avec_phrase"] = form.cleaned_data.get("avec_phrase", False)

        return context


class InfotriPreviewView(TemplateView):
    """
    Preview view that renders the Info-tri visual.
    Called via Turbo Frame to update preview dynamically.
    """

    template_name = "infotri/components/preview.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # Get parameters from query string
        context["categorie"] = self.request.GET.get("categorie", "")
        context["consigne"] = self.request.GET.get("consigne", "")
        context["avec_phrase"] = (
            self.request.GET.get("avec_phrase", "false").lower() == "true"
        )

        return context


class InfotriEmbedView(TemplateView):
    """
    Embed view that displays the actual Info-tri visual.
    This is loaded in an iframe on third-party sites.
    """

    template_name = "ui/pages/infotri_embed.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # Get parameters from query string
        context["categorie"] = self.request.GET.get("categorie", "")
        context["consigne"] = self.request.GET.get("consigne", "")
        context["avec_phrase"] = (
            self.request.GET.get("avec_phrase", "false").lower() == "true"
        )

        return context
