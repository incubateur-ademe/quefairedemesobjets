from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import (
    TrigramSimilarity,
    TrigramStrictWordSimilarity,
)
from django.db.models import Case, F, Value, When

from .models import ProduitPage, Synonyme


class HomeSearchMixin:
    """Mixin for searching products and synonyms on the homepage.

    This mixin provides a unified search implementation used by both
    the HomeSearchForm and AutocompleteHomeSearchView to ensure consistent
    search behavior.
    """

    DEFAULT_LIMIT = 10
    SYNONYME_SIMILARITY_THRESHOLD = 0.1

    def search_home(self, query: str, *, limit: int = DEFAULT_LIMIT) -> list:
        """Search for products and synonyms matching the query.

        Args:
            query: The search query string.
            limit: Maximum number of results to return.

        Returns:
            Combined list of ProduitPage and Synonyme results.
        """
        if not query:
            return []

        pages = self._search_pages(query)
        synonymes = self._search_synonymes(query)

        return (pages + synonymes)[:limit]

    def _search_pages(self, query: str) -> list:
        """Search in ProduitPages using the autocomplete method."""
        return list(ProduitPage.objects.live().autocomplete(query))

    def _search_synonymes(self, query: str) -> list[dict]:
        """Search in Synonymes using trigram similarity.

        Uses trigram similarity for fuzzy matching and boosts scores
        for matches at the start or end of the name.
        """
        return list(
            Synonyme.objects.annotate(
                word_similarity=TrigramStrictWordSimilarity(query, "nom"),
                similarity=TrigramSimilarity("nom", query),
                unaccented_nom=Unaccent("nom"),
            )
            .annotate(boosted_score=self._get_boosted_score_case(query))
            .filter(word_similarity__gte=self.SYNONYME_SIMILARITY_THRESHOLD)
            .order_by("-word_similarity", "-boosted_score", "-similarity")
            .values("nom", "boosted_score", "word_similarity", "similarity", "slug")[
                : self.DEFAULT_LIMIT
            ]
        )

    def _get_boosted_score_case(self, query: str) -> Case:
        """Create a Case expression for boosting scores based on position matches."""
        return Case(
            When(
                unaccented_nom__istartswith=query,
                then=F("similarity") + Value(0.2),
            ),
            When(
                unaccented_nom__iendswith=query,
                then=F("similarity") + Value(0.05),
            ),
            default=F("similarity"),
        )
