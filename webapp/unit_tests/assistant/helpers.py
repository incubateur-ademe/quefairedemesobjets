"""Builders shared by the assistant's tests."""

from qfdmd.models import ProduitPageSearchTerm


def rename_search_term(page, label):
    """The factory already creates the fiche's search term (one-to-one):
    rename it rather than add a second one."""
    term = ProduitPageSearchTerm.objects.get(produit_page=page)
    term.searchable_title = label
    term.save()
