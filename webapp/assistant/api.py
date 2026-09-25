"""Public API of the assistant, version 1.

The assistant's own screens are its first client: the map, the two search
fields of the header and the place pages call these endpoints. Whatever the
frontend can do, a reuser can do with the same parameters, and there is no
second code path to keep on par.

The query vocabulary is the one of the screens (`assistant/parcours.py`):
`fiche`, `geste`, `longitude`, `latitude`, plus `bbox` for the map. A screen's
query string can be forwarded as is.

Mounted at `/api/v1/` (`core/api.py`, `core/urls.py`).
"""

import json
import math
from time import perf_counter

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_control
from ninja import Field, Query, Router, Schema
from ninja.decorators import decorate_view
from ninja.pagination import paginate
from pydantic import field_validator, model_validator

from assistant.adresses import suggest_adresses
from assistant.objets import sous_categorie_ids_for, suggest_objets
from qfdmo.models.acteur import MAX_PLACES_ON_MAP, DataLicense, DisplayedActeur
from qfdmo.models.action import GroupeAction

router = Router()

CACHE_FIVE_MINUTES = cache_control(public=True, max_age=300, stale_while_revalidate=60)

# Leaflet bbox shape, as sent by the map: corner, axis, absolute bound.
BBOX_CORNERS = (
    ("southWest", "lng", 180),
    ("southWest", "lat", 90),
    ("northEast", "lng", 180),
    ("northEast", "lat", 90),
)


class LieuxQuery(Schema):
    """Where and what to search: the same words as the screens' URLs.

    The position is either the visible area (`bbox`, as sent by the map) or a
    point (`longitude`, `latitude`). An unreadable bbox is refused rather than
    falling back on the point: the fallback would hide a client bug and show
    an area the user is not looking at.
    """

    # ponytail: not validated against GroupeAction, that would cost the
    # endpoint its single query. An unknown code yields an empty collection.
    geste: list[str] = Field(
        ...,
        description="Code d'un GroupeAction (`/gestes`). Répétable : "
        "`?geste=reparer&geste=trier`.",
    )
    fiche: str = Field(
        "",
        description="Slug d'une fiche objet : restreint les lieux à ses "
        "sous-catégories. Inconnu : 404.",
    )
    longitude: float | None = Field(None, ge=-180, le=180)
    latitude: float | None = Field(None, ge=-90, le=90)
    bbox: str | None = Field(
        None,
        description="Zone visible, JSON : "
        '`{"southWest":{"lng":…,"lat":…},"northEast":{"lng":…,"lat":…}}`. '
        "Prime sur le point.",
    )

    @field_validator("geste")
    @classmethod
    def clean_geste(cls, codes: list[str]) -> list[str]:
        codes = [code.strip() for code in codes if code.strip()]
        if not codes:
            raise ValueError("geste required")
        return codes

    @field_validator("bbox")
    @classmethod
    def clean_bbox(cls, raw: str | None) -> list[float] | None:
        """Leaflet shape to four floats: west, south, east, north."""
        if raw is None:
            return None
        try:
            corners = json.loads(raw)
            bbox = [float(corners[corner][axis]) for corner, axis, _ in BBOX_CORNERS]
        except (ValueError, KeyError, TypeError):
            raise ValueError("unreadable bbox")
        for value, (_, _, bound) in zip(bbox, BBOX_CORNERS):
            if not math.isfinite(value) or abs(value) > bound:
                raise ValueError("bbox out of range")
        return bbox

    @model_validator(mode="after")
    def position_required(self):
        if self.bbox is None and None in (self.longitude, self.latitude):
            raise ValueError("bbox or longitude/latitude required")
        return self

    def queryset(self):
        """The places, through the same manager as every screen."""
        ids = sous_categorie_ids_for(self.fiche) if self.fiche else []
        acteurs = DisplayedActeur.objects.all().proposing(self.geste, ids)
        if self.bbox:
            return acteurs.within(self.bbox)
        return acteurs.nearest_to(self.longitude, self.latitude)


class PropositionSchema(Schema):
    action: str
    sous_categories: list[str]


class PerimetreSchema(Schema):
    type: str
    valeur: str


class LieuSchema(Schema):
    """A place, with the columns of the opendata dataset.

    Field names follow the CSV published on data.ademe.fr so that a reuser
    can switch between the two without a mapping. Not carried over: the
    columns data.ademe.fr computes after export (région, département, état
    SIRENE) and the per-action columns, which `propositions_de_services`
    already holds.
    """

    identifiant: str = Field(..., alias="uuid")
    paternite: str
    nom: str
    nom_commercial: str | None = None
    siren: str | None = None
    siret: str | None = None
    description: str | None = None
    type_dacteur: str | None = Field(None, alias="acteur_type.code")
    site_web: str | None = Field(None, alias="url")
    telephone: str | None = None
    adresse: str | None = None
    complement_dadresse: str | None = Field(None, alias="adresse_complement")
    code_postal: str | None = None
    ville: str | None = None
    code_commune: str | None = Field(None, alias="code_commune_insee")
    code_epci: str | None = Field(None, alias="epci.code")
    nom_epci: str | None = Field(None, alias="epci.nom")
    latitude: float | None = None
    longitude: float | None = None
    qualites_et_labels: str
    propose_le_bonus_reparation: bool
    public_accueilli: str | None = None
    reprise: str | None = None
    exclusivite_de_reprisereparation: bool | None = None
    uniquement_sur_rdv: bool | None = None
    type_de_services: str
    lieu_prestation: str | None = None
    perimetreadomicile: list[PerimetreSchema]
    consignes_dacces: str | None = None
    horaires_description: str | None = None
    horaires_osm: str | None = None
    propositions_de_services: list[PropositionSchema]
    date_de_derniere_modification: str

    @staticmethod
    def resolve_paternite(obj) -> str:
        """Same string as the dataset: the site, ADEME, then the open sources."""
        libelles = sorted(
            {
                source.libelle
                for source in obj.sources.all()
                if source.licence == DataLicense.OPEN_LICENSE
            }
        )
        return "|".join(["Que faire de mes objets et déchets", "ADEME", *libelles])

    @staticmethod
    def resolve_latitude(obj) -> float | None:
        return obj.location.y if obj.location else None

    @staticmethod
    def resolve_longitude(obj) -> float | None:
        return obj.location.x if obj.location else None

    @staticmethod
    def resolve_qualites_et_labels(obj) -> str:
        return "|".join(sorted({label.code for label in obj.labels.all()}))

    @staticmethod
    def resolve_propose_le_bonus_reparation(obj) -> bool:
        # Annotated by `with_bonus()`; a bare instance has no bonus.
        return bool(getattr(obj, "bonus", False))

    @staticmethod
    def resolve_type_de_services(obj) -> str:
        return "|".join(sorted({service.code for service in obj.acteur_services.all()}))

    @staticmethod
    def resolve_perimetreadomicile(obj) -> list[dict]:
        return [
            {"type": perimetre.type, "valeur": perimetre.valeur}
            for perimetre in obj.perimetre_adomiciles.all()
        ]

    @staticmethod
    def resolve_propositions_de_services(obj) -> list[dict]:
        return [
            {
                "action": proposition.action.code,
                "sous_categories": sorted(
                    sous_categorie.code
                    for sous_categorie in proposition.sous_categories.all()
                ),
            }
            for proposition in obj.proposition_services.all()
        ]

    @staticmethod
    def resolve_date_de_derniere_modification(obj) -> str:
        return obj.modifie_le.date().isoformat()


class GesteSchema(Schema):
    code: str
    libelle: str
    libelle_court: str | None = None
    couleur: str | None = None


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
    "/lieux",
    response=list[LieuSchema],
    url_name="lieux",
    summary="Lieux proposant un geste, du plus proche au plus lointain",
)
@decorate_view(CACHE_FIVE_MINUTES)
@paginate
def lieux(request, query: Query[LieuxQuery]):
    """Les mêmes lieux que l'assistant affiche, restreints aux sources sous
    licence ouverte : le périmètre du jeu de données publié sur data.ademe.fr.

    Triés par proximité du point donné, ou du centre de la zone `bbox`.
    """
    return query.queryset().open_data().for_the_api()


@router.get(
    "/lieux.geojson",
    url_name="lieux-geojson",
    summary="Lieux pour la carte, en GeoJSON",
)
@decorate_view(CACHE_FIVE_MINUTES)
def lieux_geojson(request, response: HttpResponse, query: Query[LieuxQuery]):
    """Au plus 20 lieux (#3356), toutes sources confondues : ce que la carte
    de l'assistant dessine. Les propriétés se limitent à ce que la punaise
    affiche ; le détail est sur `/lieux/{identifiant}`.
    """
    start = perf_counter()
    payload = query.queryset().for_the_map(MAX_PLACES_ON_MAP).as_geojson()
    duration_ms = (perf_counter() - start) * 1000
    # Read by the browser (Network tab, PerformanceObserver) and by the map's
    # debug overlay.
    response["Server-Timing"] = f'acteurs;dur={duration_ms:.1f};desc="lieux"'
    return payload


@router.get(
    "/lieux/{identifiant}",
    response=LieuSchema,
    url_name="lieu",
    summary="Un lieu",
)
@decorate_view(CACHE_FIVE_MINUTES)
def lieu(request, identifiant: str):
    """Le lieu portant cet identifiant, s'il est sous licence ouverte."""
    return get_object_or_404(
        DisplayedActeur.objects.all().open_data().for_the_api(), uuid=identifiant
    )


@router.get(
    "/gestes",
    response=list[GesteSchema],
    url_name="gestes",
    summary="Les gestes, valeurs du paramètre `geste`",
)
def gestes(request):
    return GroupeAction.objects.order_by("order")


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
