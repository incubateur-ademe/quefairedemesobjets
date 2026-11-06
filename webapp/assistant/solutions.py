"""What the solutions screen shows: the gestes asked for and the nearest
places. The map fetches its own places; the view renders them for the
accessible list."""

from django.db.models import QuerySet
from django.http import Http404, QueryDict

from assistant.forms import MISSING_ADRESSE_MESSAGE, UNKNOWN_ADRESSE_MESSAGE
from assistant.objets import fiche_for_label
from assistant.parcours import Parcours
from qfdmo.lieux_query import sous_categorie_ids_for
from qfdmo.models.acteur import DisplayedActeur
from qfdmo.models.action import GroupeAction

PARIS = (2.3488, 48.8534)


def requested_gestes(query: QueryDict) -> list[str]:
    """The `geste` parameters, stripped, once each, in their order."""
    codes = (code.strip() for code in query.getlist("geste"))
    return list(dict.fromkeys(code for code in codes if code))


def groupes_in_order(codes: list[str]) -> list[GroupeAction]:
    by_code = {g.code: g for g in GroupeAction.objects.filter(code__in=codes)}
    return [by_code[code] for code in codes if code in by_code]


def label_of(block: dict | None, groupes: list[GroupeAction]) -> str:
    if block:
        return block["libelle"]
    if groupes:
        return groupes[0].libelle_court or groupes[0].libelle
    return ""


def fiche_slug_for(label: str) -> str:
    """The fiche a label designates, for a shared URL carrying only the text."""
    fiche = fiche_for_label(label) if label else None
    return fiche.slug if fiche else ""


def sous_categorie_ids_of(slug: str) -> list[int]:
    """An unknown fiche narrows nothing: the screen still shows its places."""
    try:
        return sous_categorie_ids_for(slug) if slug else []
    except Http404:
        return []


def nearest_lieux(
    gestes: list[str], slug: str, longitude: float, latitude: float
) -> QuerySet[DisplayedActeur] | list:
    if not gestes:
        return []
    return (
        DisplayedActeur.objects.all()
        .proposing(gestes, sous_categorie_ids_of(slug))
        .nearest_to(longitude, latitude)
        .for_the_map()
    )


def position_of(parcours: Parcours) -> tuple[float, float]:
    if parcours.is_located:
        return parcours.longitude, parcours.latitude
    return PARIS


def address_error(parcours: Parcours) -> str:
    if parcours.is_located:
        return ""
    return UNKNOWN_ADRESSE_MESSAGE if parcours.adresse else MISSING_ADRESSE_MESSAGE
