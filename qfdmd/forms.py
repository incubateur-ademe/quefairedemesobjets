import logging

from django import forms
from django.contrib.postgres.search import (
    TrigramSimilarity,
    TrigramStrictWordSimilarity,
)
from dsfr.forms import DsfrBaseForm

logger = logging.getLogger(__name__)


class SearchInput(forms.TextInput):
    template_name = "components/search/widget.html"


class SearchForm(DsfrBaseForm):
    input = forms.CharField(
        help_text="Entrez un objet ou un déchet", required=False, widget=SearchInput
    )

    def clean(self):
        from .models import Synonyme

        search_query: str = self.cleaned_data.get("input")
        self.results = (
            Synonyme.objects.annotate(
                word_similarity=TrigramStrictWordSimilarity(search_query, "nom"),
                similarity=TrigramSimilarity("nom", search_query),
            )
            .filter(word_similarity__gte=0.1)
            .order_by("-word_similarity", "-similarity")
            .values("slug", "nom")[:10]
        )
        return super().clean()
