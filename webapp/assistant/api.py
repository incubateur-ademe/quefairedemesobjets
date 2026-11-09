"""API v1 endpoints of the assistant's screens: the map and the two search
fields. Same query vocabulary as the screens' URLs (`qfdmo/lieux_query.py`)."""

from time import perf_counter

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.http import HttpResponse
from ninja import Query, Router, Schema
from ninja.decorators import decorate_view

from assistant.adresses import suggest_adresses
from assistant.objets import suggest_objets
from core.http_cache import CACHE_FIVE_MINUTES, CACHE_ONE_HOUR
from qfdmo.lieux_query import LieuxQuery
from qfdmo.models.acteur import MAX_PLACES_ON_MAP

router = Router()

RADIUS_KM = 20


class SuggestionObjet(Schema):
    label: str
    slug: str
    synonyme: str | None = None


class SuggestionAdresse(Schema):
    label: str
    detail: str
    longitude: float
    latitude: float
    precise: bool


class SuggestionsObjets(Schema):
    results: list[SuggestionObjet]


class SuggestionsAdresses(Schema):
    results: list[SuggestionAdresse]


@router.get(
    "/lieux.geojson",
    url_name="lieux-geojson",
    summary="Lieux pour la carte, en GeoJSON",
)
@decorate_view(CACHE_FIVE_MINUTES)
def lieux_geojson(request, response: HttpResponse, query: Query[LieuxQuery]):
    """Au plus 20 lieux, toutes sources confondues : ce que la carte de
    l'assistant dessine. Autour d'un point, les plus proches à moins de 20 km.
    `geste` est le premier des gestes demandés que le lieu propose, pour l'objet
    de la fiche s'il y en a une. Le détail d'un lieu est sur `/lieux/{identifiant}`.
    """
    start = perf_counter()
    acteurs = query.queryset().with_geste(query.geste, query.sous_categorie_ids)
    if query.bbox is None:
        position = Point(query.longitude, query.latitude, srid=4326)
        acteurs = acteurs.annotate(distance=Distance("location", position))
    places = acteurs.for_the_map(MAX_PLACES_ON_MAP)
    if query.bbox is None:
        # Filtered after the LIMIT: an `ST_DWithin` bound would prevent the
        # ordered index scan of `nearest_to`.
        places = [place for place in places if place.distance.km <= RADIUS_KM]
    payload = {
        "type": "FeatureCollection",
        "features": [place.as_geojson_feature() for place in places],
    }
    duration_ms = (perf_counter() - start) * 1000
    response["Server-Timing"] = f'acteurs;dur={duration_ms:.1f};desc="lieux"'
    return payload


@router.get(
    "/objets",
    response=SuggestionsObjets,
    exclude_none=True,
    url_name="objets",
    summary="Suggestions d'objets pour une saisie",
)
@decorate_view(CACHE_FIVE_MINUTES)
def objets(request, q: str = ""):
    """Sept suggestions au plus, dès deux caractères. `slug` est la valeur
    attendue par le paramètre `fiche`."""
    return {"results": suggest_objets(q)}


@router.get(
    "/adresses",
    response=SuggestionsAdresses,
    url_name="adresses",
    summary="Suggestions d'adresses pour une saisie",
)
@decorate_view(CACHE_ONE_HOUR)
def adresses(request, q: str = ""):
    """Cinq suggestions au plus, dès trois caractères, via la Base Adresse
    Nationale. `precise` distingue une adresse d'une commune."""
    return {"results": suggest_adresses(q)}
