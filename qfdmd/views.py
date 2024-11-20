import logging
from typing import Any

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import DetailView, TemplateView

from qfdmd.forms import SearchForm
from qfdmd.models import Synonyme

logger = logging.getLogger(__name__)


def generate_iframe_script() -> str:
    return '<script id="datagir_dechets" '
    'src="https://quefairedemesdechets.ademe.fr/iframe.js" '
    'data-search="?theme=default"></script>'


SEARCH_VIEW_TEMPLATE_NAME = "components/search/view.html"


def search_view(request) -> HttpResponse:
    form = SearchForm(request.GET)
    context = {}
    template_name = SEARCH_VIEW_TEMPLATE_NAME

    if form.is_valid():
        context.update(search_form=form)

    return render(request, template_name, context=context)


class BaseView:
    """Base view that provides templates used on all pages.
    TODO: this could be moved to a context processor"""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            search_form=SearchForm(),
            search_view_template_name=SEARCH_VIEW_TEMPLATE_NAME,
        )
        return context


class HomeView(BaseView, TemplateView):
    pass


class SynonymeDetailView(BaseView, DetailView):
    model = Synonyme

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(iframe_script=generate_iframe_script())
        return context
