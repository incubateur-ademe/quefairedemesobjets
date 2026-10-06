"""Resolution of an objet label to its fiche.

Lives outside the `views` package: the form needs it, and `views/__init__`
imports the views that import the form. Keeping it there created a cycle.
"""

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
    """The `ProduitPage` of a term, or None if it targets none."""
    from django.core.exceptions import ObjectDoesNotExist

    for relation in FICHE_RELATIONS:
        try:
            page = getattr(term, relation, None)
        except ObjectDoesNotExist:
            continue
        if page is not None and getattr(page, "slug", None):
            return page
    return None
