import logging
from typing import Any

from django import forms
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import (
    TrigramSimilarity,
    TrigramStrictWordSimilarity,
)
from django.db.models import Case, F, Value, When
from dsfr.forms import DsfrBaseForm

from .models import ProduitPage, Synonyme

logger = logging.getLogger(__name__)


class SearchInput(forms.TextInput):
    template_name = "ui/components/search/widget.html"


class SearchForm(DsfrBaseForm):
    id = forms.CharField(required=False, widget=forms.HiddenInput())
    input = forms.CharField(
        help_text="Entrez un objet ou un déchet",
        required=False,
        widget=SearchInput,
    )

    def search(self, beta: bool) -> list[dict[str, Any]]:
        """Main search method that orchestrates the search process."""
        search_query = self.cleaned_data.get("input")
        if not search_query:
            return []

        if beta:
            self.results = self._search_pages(search_query)
        else:
            self.results = self._search_legacy_synonymes(search_query)
        return self.results

    def _search_pages(self, search_query: str):
        return list(
            ProduitPage.objects.live().autocomplete(search_query)
        ) + self._search_legacy_synonymes(search_query)

    def _search_legacy_synonymes(self, search_query: str):
        return list(
            Synonyme.objects.annotate(
                word_similarity=TrigramStrictWordSimilarity(search_query, "nom"),
                similarity=TrigramSimilarity("nom", search_query),
                unaccented_nom=Unaccent("nom"),
            )
            .annotate(boosted_score=self._get_boosted_score_case(search_query))
            .filter(word_similarity__gte=0.1)
            .order_by("-word_similarity", "-boosted_score", "-similarity")
            .values("nom", "boosted_score", "word_similarity", "similarity", "slug")[
                :10
            ]
        )

    def _get_boosted_score_case(self, search_query: str) -> Case:
        """Create a Case expression for boosting scores based on position matches."""
        return Case(
            When(
                unaccented_nom__istartswith=search_query,
                then=F("similarity") + Value(0.2),
            ),
            When(
                unaccented_nom__iendswith=search_query,
                then=F("similarity") + Value(0.05),
            ),
            default=F("similarity"),
        )


class ContactForm(DsfrBaseForm):
    name = forms.CharField(label="Votre nom")
    name.widget.attrs["autocomplete"] = "name"
    email = forms.EmailField(label="Votre email")
    email.widget.attrs["autocomplete"] = "email"
    subject = forms.ChoiceField(
        label="Votre sujet",
        choices=[
            ("", "Sélectionner une option"),
            (
                "integration",
                "Je souhaite obtenir de l'aide pour intégrer cet outil",
            ),
            (
                "erreur",
                "Je souhaite signaler une erreur pour un déchet",
            ),
            (
                "manquant",
                "Je souhaite signaler un déchet manquant",
            ),
            (
                "bug",
                "J'ai trouvé un bug",
            ),
            (
                "amelioration",
                "Je souhaite proposer une amélioration",
            ),
            (
                "autre",
                "Autre",
            ),
        ],
    )
    message = forms.CharField(
        label="Votre message", widget=forms.Textarea(attrs={"rows": 4})
    )
