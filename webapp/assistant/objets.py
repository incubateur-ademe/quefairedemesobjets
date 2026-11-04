"""Objets: from what the user types to a fiche and its synonymes."""

from django.core.exceptions import ObjectDoesNotExist

from qfdmd.models import ProduitPageSearchTerm, SearchTag, Synonyme

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


def synonyme_of_term(term_id, fiche):
    """The synonyme behind a `SearchTerm` id (the site search's cookie), if it
    leads to `fiche`, else None."""
    specific = _specifics([term_id]).get(term_id) if term_id else None
    if specific is None or not _is_synonyme(specific):
        return None
    return specific if _leads_to(specific, fiche) else None


def _leads_to(term, fiche) -> bool:
    page = fiche_of(term)
    return page is not None and page.pk == fiche.pk
