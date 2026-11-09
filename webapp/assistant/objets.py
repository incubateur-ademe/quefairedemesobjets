"""Objets: from what the user types to the fiche it designates."""

from django.core.exceptions import ObjectDoesNotExist
from django.db import OperationalError, connection, transaction
from modelsearch.query import Fuzzy

from qfdmd.models import ProduitPageSearchTerm, SearchTag, Synonyme
from search.models import SearchTerm

RESULTS_COUNT = 7
MIN_LENGTH = 2
MAX_LENGTH = 100
SEARCH_TIMEOUT_MS = 300

# Each SearchTerm subclass names its label and its fiche differently.
LABEL_FIELDS = (
    (ProduitPageSearchTerm, "searchable_title"),
    (SearchTag, "name"),
    (Synonyme, "nom"),
)
FICHE_RELATIONS = ("produit_page", "page")


def capitalize_first(text: str) -> str:
    """`str.capitalize()` would also lower the rest: « Bonus Réparation »."""
    return text[:1].upper() + text[1:]


def fiche_of(term):
    """The live `ProduitPage` a term leads to, or None."""
    for relation in FICHE_RELATIONS:
        try:
            page = getattr(term, relation, None)
        except ObjectDoesNotExist:
            continue
        if page is not None and getattr(page, "slug", None) and page.live:
            return page
    return None


def suggest_objets(query: str) -> list[dict]:
    """Objet suggestions for a typed text; an empty list below two characters
    or when the search exceeds its time budget."""
    query = (query or "").strip()[:MAX_LENGTH]
    if len(query) < MIN_LENGTH:
        return []

    # `SET LOCAL` lasts until the end of the transaction: the timeout and the
    # search must share one, autocommit would drop it before the search.
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout = %s", [SEARCH_TIMEOUT_MS])
            terms = list(
                SearchTerm.objects.searchable().search(Fuzzy(query, unaccent=True))[
                    :RESULTS_COUNT
                ]
            )
            specifics = _specifics([term.id for term in terms])
    except OperationalError:
        return []

    suggestions = (_suggestion(specifics.get(term.id)) for term in terms)
    return [suggestion for suggestion in suggestions if suggestion]


def _specifics(ids: list[int]) -> dict[int, object]:
    """The subclass instance of each term, one query per subclass rather than
    up to three per term with `SearchTerm.specific`. Same priority order as
    `get_indexed_instance`."""
    resolved: dict[int, object] = {}
    for model, _ in LABEL_FIELDS:
        missing = [term_id for term_id in ids if term_id not in resolved]
        if not missing:
            break
        for instance in model.objects.filter(searchterm_ptr_id__in=missing):
            resolved[instance.searchterm_ptr_id] = instance
    return resolved


def _suggestion(specific) -> dict | None:
    """Label and fiche of a term; None when it leads to no live fiche."""
    if specific is None:
        return None
    label = specific.get_title()
    page = fiche_of(specific)
    if not label or page is None:
        return None

    return {"label": capitalize_first(label), "slug": page.slug}
