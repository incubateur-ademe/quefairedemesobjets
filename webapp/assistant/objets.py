"""Objets: from what the user types to a fiche and its synonymes."""

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


def fiche_for_label(label: str):
    """The fiche of a term matching `label` exactly, for a URL carrying only
    the text. Exact rather than fuzzy: a guess would open the wrong fiche."""
    for model, field in LABEL_FIELDS:
        for term in model.objects.filter(**{f"{field}__iexact": label})[:5]:
            if page := fiche_of(term):
                return page
    return None


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


def _is_synonyme(specific) -> bool:
    return not isinstance(specific, ProduitPageSearchTerm)


def _suggestion(specific) -> dict | None:
    """Label and fiche of a term; None when it leads to no live fiche."""
    if specific is None:
        return None
    label = specific.get_title()
    page = fiche_of(specific)
    if not label or page is None:
        return None

    suggestion = {"label": capitalize_first(label), "slug": page.slug}
    if _is_synonyme(specific):
        suggestion["synonyme"] = specific.slug
    return suggestion


def synonyme_of(slug: str, fiche):
    """The synonyme named by `slug`, if it still leads to `fiche`, else None:
    a synonyme removed or moved since the URL was shared is ignored.
    `SearchTag` first: the tags imported from `Synonyme` reuse its slugs."""
    if not slug:
        return None
    for model in (SearchTag, Synonyme):
        for term in model.objects.filter(slug=slug)[:5]:
            if _leads_to(term, fiche):
                return term
    return None


def synonyme_of_term(term_id, fiche):
    """The synonyme behind a `SearchTerm` id (the site search's cookie), if it
    leads to `fiche`, else None."""
    specific = _specifics([term_id]).get(term_id) if term_id else None
    if specific is None or not _is_synonyme(specific):
        return None
    return specific if _leads_to(specific, fiche) else None


def synonyme_label(slug: str, fiche) -> str:
    term = synonyme_of(slug, fiche)
    return capitalize_first(term.get_title() or "") if term else ""


def _leads_to(term, fiche) -> bool:
    page = fiche_of(term)
    return page is not None and page.pk == fiche.pk
