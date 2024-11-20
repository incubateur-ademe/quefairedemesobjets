import logging
from typing import Any

from django.http import HttpResponse
from django.views.generic import DetailView, FormView, TemplateView

from qfdmd.forms import SearchForm
from qfdmd.models import Synonyme

logger = logging.getLogger(__name__)


def generate_iframe_script() -> str:
    return '<script id="datagir_dechets" '
    'src="https://quefairedemesdechets.ademe.fr/iframe.js" '
    'data-search="?theme=default"></script>'


class BaseView:
    """Base view that provides templates used on all pages.
    TODO: this could be moved to a context processor"""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            search_form=SearchForm(),
            search_view_template_name=SearchFormView.template_name,
        )
        return context


class SearchFormView(FormView):
    form_class = SearchForm
    template_name = "components/search/view.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # TODO : ajouter commentaire en expliquant pourquoi on fait ça
        context["search_form"] = context.pop("form")
        return context

    def form_valid(self, form: SearchForm) -> HttpResponse:
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class HomeView(BaseView, TemplateView):
    pass


class SynonymeDetailView(BaseView, DetailView):
    model = Synonyme

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(iframe_script=generate_iframe_script())
        return context
