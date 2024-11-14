from typing import Any

from django.views.generic import DetailView, TemplateView

from qfdmd.forms import SearchForm
from qfdmd.models import Synonyme


class SearchFormMixin:
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        search_form = SearchForm()
        context.update(search_form=search_form)
        return context


class HomeView(TemplateView):
    pass


class SynonymeDetailView(SearchFormMixin, DetailView):
    model = Synonyme
