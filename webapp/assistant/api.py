"""API v1 endpoints of the assistant's screens: the map, the counters of the
fiche's buttons and the two search fields of the header.

The query vocabulary is the one of the screens (`assistant/parcours.py`),
shared with the open data of the places (`opendata/api.py`) through
`qfdmo/lieux_query.py`. A screen's query string can be forwarded as is.

Mounted at `/api/v1/` (`core/api.py`, `core/urls.py`).
"""

from time import perf_counter

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from ninja import Field, Query, Router, Schema
from ninja.decorators import decorate_view
from pydantic import field_validator

from assistant.adresses import suggest_adresses
from assistant.compte import RADIUS_KM, count_nearby
from assistant.objets import suggest_objets
from qfdmo.lieux_query import LieuxQuery, clean_codes, sous_categorie_ids_for
from qfdmo.models.acteur import MAX_PLACES_ON_MAP

router = Router()

CACHE_FIVE_MINUTES = cache_control(public=True, max_age=300, stale_while_revalidate=60)


class CompteQuery(Schema):
    """Same words as `LieuxQuery`, but a point is required: "à proximité" is
    a radius around the address, not a map area."""

    geste: list[str] = Field(..., description="Code d'un GroupeAction, répétable.")
    fiche: str = Field("", description="Slug d'une fiche objet. Inconnu : 404.")
    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)

    @field_validator("geste")
    @classmethod
    def clean_geste(cls, codes: list[str]) -> list[str]:
        return clean_codes(codes)


class CompteSchema(Schema):
    count: int


class SuggestionObjet(Schema):
    label: str
    slug: str


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
    """Au plus 20 lieux (#3356), toutes sources confondues : ce que la carte
    de l'assistant dessine. Autour d'un point, les 20 plus proches à moins de
    20 km : le premier affichage de la carte, cadré sur eux. Les propriétés se
    limitent à ce que la punaise affiche ; le détail est sur
    `/lieux/{identifiant}`.
    """
    start = perf_counter()
    acteurs = query.queryset()
    if query.bbox is None:
        position = Point(query.longitude, query.latitude, srid=4326)
        acteurs = acteurs.annotate(distance=Distance("location", position))
    places = acteurs.for_the_map(MAX_PLACES_ON_MAP)
    if query.bbox is None:
        # ponytail: filtered after the LIMIT, a `ST_DWithin` would cost the
        # KNN scan of the GiST index (see `nearest_to`). 20 rows at most.
        places = [place for place in places if place.distance.km <= RADIUS_KM]
    payload = {
        "type": "FeatureCollection",
        "features": [place.as_geojson_feature() for place in places],
    }
    duration_ms = (perf_counter() - start) * 1000
    # Read by the browser (Network tab, PerformanceObserver) and by the map's
    # debug overlay.
    response["Server-Timing"] = f'acteurs;dur={duration_ms:.1f};desc="lieux"'
    return payload


@router.get(
    "/lieux/compte",
    response=CompteSchema,
    url_name="lieux-compte",
    summary="Nombre de lieux à moins de 20 km",
)
@decorate_view(CACHE_FIVE_MINUTES)
def lieux_compte(request, query: Query[CompteQuery]):
    """Ce que le bouton d'un bloc de la fiche affiche une fois la page rendue
    (ADR 0010) : le compte est approché, par maille d'environ un kilomètre,
    et mis en cache 12 h."""
    ids = sous_categorie_ids_for(query.fiche) if query.fiche else []
    return {"count": count_nearby(query.geste, ids, query.longitude, query.latitude)}


@router.get(
    "/objets",
    response=SuggestionsObjets,
    url_name="objets",
    summary="Suggestions d'objets pour une saisie",
)
@decorate_view(CACHE_FIVE_MINUTES)
def objets(request, response: HttpResponse, q: str = ""):
    """Sept suggestions au plus, dès deux caractères. `slug` est la valeur
    attendue par le paramètre `fiche`."""
    start = perf_counter()
    results = suggest_objets(q)
    response["Server-Timing"] = f"recherche;dur={(perf_counter() - start) * 1000:.1f}"
    return {"results": results}


@router.get(
    "/adresses",
    response=SuggestionsAdresses,
    url_name="adresses",
    summary="Suggestions d'adresses pour une saisie",
)
@decorate_view(cache_control(public=True, max_age=60 * 60, stale_while_revalidate=300))
def adresses(request, q: str = ""):
    """Cinq suggestions au plus, dès trois caractères, via la Base Adresse
    Nationale. `precise` distingue une adresse d'une commune."""
    return {"results": suggest_adresses(q)}
