"""Objets: from what the user types to a fiche and its sous-catégories.

Lives outside the `views` package: the form needs it, and `views/__init__`
imports the views that import the form. Keeping it there created a cycle.
"""

from django.http import Http404

RESULTS_COUNT = 7
MIN_LENGTH = 2
MAX_LENGTH = 100
SEARCH_TIMEOUT_MS = 300

# Each SearchTerm subclass names its label differently: there is no common
# field to query.
LABEL_FIELDS = (
    ("ProduitPageSearchTerm", "searchable_title"),
    ("SearchTag", "name"),
    ("Synonyme", "nom"),
)

# Each subclass also names its relation to the fiche differently.
FICHE_RELATIONS = ("produit_page", "page")


def fiche_for_label(label: str):
    """Fiche matching an exact label, for a shared URL.

    Returns the `ProduitPage` itself, not its slug: the caller needs it as is,
    and handing it over avoids reloading it right after.

    The autocomplete returns the slug with each suggestion; this path serves
    when the user arrives through a link that only carries the text. The
    lookup is exact, not fuzzy: guessing on an approximate input would open
    the wrong fiche without the user understanding why.
    """
    from qfdmd import models

    # Each subclass stores its label in a different field: three indexed
    # queries beat scanning the 2,271 terms in Python, which cost 263 ms.
    for model_name, field in LABEL_FIELDS:
        model = getattr(models, model_name)
        for term in model.objects.filter(**{f"{field}__iexact": label})[:5]:
            if page := fiche_of(term):
                return page
    return None


def fiche_of(term):
    """The live `ProduitPage` of a term, or None if it targets none.

    A draft or unpublished fiche is not a destination: every other lookup of
    the app goes through `ProduitPage.objects.live()`, and routing to a page
    that then 404s would be worse than "unknown objet".
    """
    from django.core.exceptions import ObjectDoesNotExist

    for relation in FICHE_RELATIONS:
        try:
            page = getattr(term, relation, None)
        except ObjectDoesNotExist:
            continue
        if page is not None and getattr(page, "slug", None) and page.live:
            return page
    return None


def sous_categorie_ids_for(slug: str) -> list[int]:
    """Sous-catégories of the fiche, to narrow the places to that objet.

    A fiche without sous-catégorie returns an empty list: the places are then
    not narrowed, rather than showing none.
    """
    from qfdmd.models import ProduitPage

    page = ProduitPage.objects.live().filter(slug=slug).first()
    if page is None:
        raise Http404(f"unknown objet: {slug}")
    return list(page.sous_categorie_objet.values_list("id", flat=True))


def suggest_objets(query: str) -> list[dict]:
    """Objet suggestions for a typed text, or an empty list below two characters.

    Served as JSON (ADR 0007): Django templating cost more than the query
    itself (~25 ms against 15 ms), and the client knows how to build its list.

    The `statement_timeout` bounds the query rather than letting a pathological
    search block typing: better an empty list than a frozen field.
    """
    from django.db import OperationalError, connection, transaction
    from modelsearch.query import Fuzzy

    from search.models import SearchTerm

    query = (query or "").strip()[:MAX_LENGTH]
    if len(query) < MIN_LENGTH:
        return []

    # `SET LOCAL` only lasts until the end of the current transaction: in
    # autocommit mode it would be discarded before the search runs. The
    # timeout and the search must share one transaction.
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


def _suggestion(specific) -> dict | None:
    """Label and target fiche of a term.

    `SearchTerm` is a base: only its subclasses know how to produce a title.
    Without going through the subclass, every label comes out empty.

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
