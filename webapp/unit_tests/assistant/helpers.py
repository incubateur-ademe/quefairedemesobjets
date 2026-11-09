"""Builders and HTML readers shared by the assistant's tests."""

from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup
from django.contrib.gis.geos import Point

from qfdmd.models import ProduitPageSearchTerm
from unit_tests.qfdmd.qfdmod_factory import ProduitPageFactory
from unit_tests.qfdmo.acteur_factory import (
    DisplayedActeurFactory,
    DisplayedPropositionServiceFactory,
    SourceFactory,
)
from unit_tests.qfdmo.action_factory import ActionFactory, GroupeActionFactory

PARIS = {"latitude": "48.8534", "longitude": "2.3488"}
PARIS_POINT = Point(2.3488, 48.8534, srid=4326)


def html_of(response_or_html) -> BeautifulSoup:
    content = getattr(response_or_html, "content", response_or_html)
    return BeautifulSoup(content, "html.parser")


def query_of(url: str) -> dict[str, list[str]]:
    return parse_qs(urlsplit(url).query)


def field(page: BeautifulSoup, name: str):
    """The visible input of a form field (hidden ones excluded)."""
    return page.select_one(f'input[name="{name}"]:not([type="hidden"])')


def error_of(page: BeautifulSoup, name: str) -> str | None:
    """The server's message under a combobox field, as opposed to the hidden
    "aucun résultat" one; None when the field shows none."""
    combobox = field(page, name).find_parent(class_="qfa-combobox")
    erreur = combobox.select_one('[data-assistant-combobox-target="erreur"]')
    return erreur.get_text(strip=True) if erreur else None


def action_of(groupe_code, action_code=None, **groupe_fields):
    """An Action and its GroupeAction. Both factories get_or_create on the code:
    an existing code brings back the existing row."""
    groupe = GroupeActionFactory(code=groupe_code, **groupe_fields)
    return ActionFactory(code=action_code or groupe_code, groupe_action=groupe)


def place_offering(
    action, *, at=PARIS_POINT, licence=None, sous_categories=(), **acteur_fields
):
    """A displayed acteur offering `action` at `at`."""
    acteur = DisplayedActeurFactory(location=at, **acteur_fields)
    if licence is not None:
        acteur.sources.add(SourceFactory(licence=licence))
    proposition = DisplayedPropositionServiceFactory(acteur=acteur, action=action)
    proposition.sous_categories.add(*sous_categories)
    return acteur


def fiche_for(sous_categories):
    """ParentalManyToManyField: the relation only exists once saved."""
    page = ProduitPageFactory(parent=None)
    page.sous_categorie_objet.set(sous_categories)
    page.save()
    return page


def rename_search_term(page, label):
    """The factory already creates the fiche's search term (one-to-one):
    rename it rather than add a second one."""
    term = ProduitPageSearchTerm.objects.get(produit_page=page)
    term.searchable_title = label
    term.save()
