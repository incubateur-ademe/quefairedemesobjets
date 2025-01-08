import logging
from typing import Any

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import DetailView, FormView, ListView

<<<<<<< HEAD
from qfdmd.forms import SearchForm
from qfdmd.models import CMSPage, Suggestion, Synonyme
=======
from qfdmd.forms import ContactForm, SearchForm
from qfdmd.models import Suggestion, Synonyme
>>>>>>> b1807f4b (Ajout du formulaire de contact dans l'assistant)

logger = logging.getLogger(__name__)


def generate_iframe_script(request) -> str:
    """Generates a <script> tag used to embed Assistant website."""
    script_parts = ["<script"]

    if request.resolver_match.view_name == "qfdmd:synonyme-detail":
        produit_slug = request.resolver_match.kwargs["slug"]
        script_parts.append(f'data-objet="{produit_slug}"')

    script_parts.append(f'src="{settings.BASE_URL}/script.js"></script>')
    return " ".join(script_parts)


SEARCH_VIEW_TEMPLATE_NAME = "components/search/view.html"


def search_view(request) -> HttpResponse:
    form = SearchForm(request.GET)
    context = {}
    template_name = SEARCH_VIEW_TEMPLATE_NAME

    if form.is_valid():
        form.search()
        context.update(search_form=form)

    return render(request, template_name, context=context)


class ContactFormView(FormView):
    template_name = "forms/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("qfdmd:nous-contacter-confirmation")

    def form_valid(self, form):
        logger.error(f"{form=}")
        return super().form_valid(form)


class BaseView:
    """Base view that provides templates used on all pages.
    TODO: this could be moved to a context processor"""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            footer_pages=CMSPage.objects.all(),
            search_form=SearchForm(),
            search_view_template_name=SEARCH_VIEW_TEMPLATE_NAME,
            iframe_script=generate_iframe_script(self.request),
        )
        return context


class HomeView(BaseView, ListView):
    template_name = "qfdmd/home.html"
    model = Suggestion

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            accordion={
                "id": "professionels",
                "title": "Je suis un professionnel",
                "content": "Actuellement, l’ensemble des recommandations ne concerne "
                "que les particuliers. Pour des informations à destination des "
                "professionnels, veuillez consulter le site "
                "<a href='https://economie-circulaire.ademe.fr/dechets-activites-economiques.'"
                "target='_blank' rel='noreferrer' "
                "title='Économie Circulaire ADEME - Nouvelle fenêtre'>"
                "https://economie-circulaire.ademe.fr/dechets-activites-economiques"
                "</a>.",
            }
        )
        return context


class SynonymeDetailView(BaseView, DetailView):
    model = Synonyme


class CMSPageDetailView(BaseView, DetailView):
    model = CMSPage
