from time import perf_counter

from django.db import OperationalError, connection
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_control
from modelsearch.query import Fuzzy

from assistant.objets import fiche_of
from search.models import SearchTerm

RESULTS_COUNT = 7
MIN_LENGTH = 2
MAX_LENGTH = 100
SEARCH_TIMEOUT_MS = 300


@method_decorator(
    cache_control(public=True, max_age=300, stale_while_revalidate=60),
    name="dispatch",
)
class ObjetSearchView(View):
    """Objet suggestions for the assistant's search bar.

    Returns JSON rather than an HTML template: Django rendering cost more than
    the query itself (~25 ms against 15 ms), and the client knows how to build
    its own list.

    The `statement_timeout` bounds the query rather than letting a pathological
    search block typing: better an empty list than a frozen field.
    """

    def get(self, request, *args, **kwargs):
        query = (request.GET.get("q") or "").strip()[:MAX_LENGTH]
        if len(query) < MIN_LENGTH:
            return JsonResponse({"results": []})

        start = perf_counter()
        results = self._search(query)
        duration_ms = (perf_counter() - start) * 1000

        response = JsonResponse({"results": results})
        response.headers["Server-Timing"] = f"recherche;dur={duration_ms:.1f}"
        return response

    def _search(self, query: str) -> list[dict]:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout = %s", [SEARCH_TIMEOUT_MS])

            terms = SearchTerm.objects.searchable().search(Fuzzy(query, unaccent=True))[
                :RESULTS_COUNT
            ]
            specifics = self._specifics([term.id for term in terms])

            suggestions = (self._suggestion(specifics.get(term.id)) for term in terms)
            return [suggestion for suggestion in suggestions if suggestion]
        except OperationalError:
            return []

    def _specifics(self, ids: list[int]) -> dict[int, object]:
        """Resolves the subclasses of all terms in three queries.

        `SearchTerm.specific` queries each subclass one after the other, up to
        three queries per term: 30 queries for 7 results. The same work batched
        takes three, whatever the number of suggestions.

        The priority order follows `get_indexed_instance`: a term present in
        several subclasses is represented by the first one.
        """
        from qfdmd.models import ProduitPageSearchTerm, SearchTag, Synonyme

        resolved: dict[int, object] = {}
        for model in (ProduitPageSearchTerm, SearchTag, Synonyme):
            missing = [term_id for term_id in ids if term_id not in resolved]
            if not missing:
                break
            for instance in model.objects.filter(searchterm_ptr_id__in=missing):
                resolved[instance.searchterm_ptr_id] = instance
        return resolved

    def _suggestion(self, specific) -> dict | None:
        """Label and target fiche of a term.

        `SearchTerm` is a base: only its subclasses know how to produce a
        title. Without going through the subclass, every label comes out empty.

        A suggestion without a fiche is not returned: it would lead to a dead
        end. That is the case of a synonyme attached to a produit of the legacy
        model rather than to a `ProduitPage`.
        """
        if specific is None:
            return None

        label = specific.get_title()
        page = fiche_of(specific)
        if not label or page is None:
            return None

        return {"label": label, "slug": page.slug}
