import math
from typing import List, Optional

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.shortcuts import get_object_or_404
from ninja import Field, FilterSchema, ModelSchema, Query, Router
from ninja.pagination import paginate

from qfdmo.admin.acteur import GenericExporterMixin
from qfdmo.geo_api import search_epci_code
from qfdmo.models import (
    ActeurService,
    ActeurStatus,
    ActeurType,
    Action,
    DisplayedActeur,
    GroupeAction,
    Source,
    SousCategorieObjet,
)

router = Router()


def distance_to_decimal_degrees(distance, latitude):
    """
    From https://gis.stackexchange.com/a/384823

    Source of formulae information:
        1. https://en.wikipedia.org/wiki/Decimal_degrees
        2. http://www.movable-type.co.uk/scripts/latlong.html
    :param distance: an instance of `from django.contrib.gis.measure.Distance`
    :param latitude: y - coordinate of a point/location
    """
    lat_radians = latitude * (math.pi / 180)
    # 1 longitudinal degree at the equator equal 111,319.5m equiv to 111.32km
    return distance.m / (111_319.5 * math.cos(lat_radians))


class ActeurTypeSchema(ModelSchema):
    class Meta:
        model = ActeurType
        fields = ["id", "code", "libelle"]


class ActionSchema(ModelSchema):
    couleur: str = Field(..., alias="primary")

    class Meta:
        model = Action
        fields = ["id", "code", "libelle", "icon"]


class GroupeActionSchema(ActionSchema):
    class Meta(ActionSchema.Meta):
        model = GroupeAction


class ActeurServiceSchema(ModelSchema):
    class Meta:
        model = ActeurService
        fields = ["id", "code", "libelle"]


class SourceSchema(ModelSchema):
    logo: Optional[str] = Field(..., alias="logo_file_absolute_url")

    class Meta:
        model = Source
        fields = ["id", "code", "libelle", "url"]


class SousCategorieObjetSchema(ModelSchema):
    class Meta:
        model = SousCategorieObjet
        fields = ["id", "code", "libelle"]


class ActeurSchema(ModelSchema):
    latitude: float
    longitude: float
    services: List[ActeurServiceSchema] = Field(
        ...,
        alias="acteur_services.all",
        description="Les services proposés pour un acteur",
    )
    actions: List[ActionSchema] = Field(
        ..., alias="acteur_actions", description="Les actions proposés pour un acteur"
    )
    type: ActeurTypeSchema = Field(
        ..., alias="acteur_type", description="Le type d'acteur"
    )
    distance: Optional[float] = None
    nom: str = Field(..., alias="libelle", description="Le nom d'affichage de l'acteur")
    adresse: str = Field(
        ..., alias="adresse_display", description="l'adresse complète de l'acteur"
    )
    sources: List[str] = Field(..., description="La paternité de l'acteur")

    @staticmethod
    def resolve_sources(obj):
        exporter = GenericExporterMixin()
        return exporter.get_sources(obj)

    @staticmethod
    def resolve_distance(obj):
        if not obj.distance:
            return
        return obj.distance.m

    class Meta:
        model = DisplayedActeur
        fields = ["nom_commercial", "identifiant_unique", "siret"]


class ActeurFilterSchema(FilterSchema):
    types: Optional[List[int]] = Field(None, q="acteur_type__in")
    services: Optional[List[int]] = Field(None, q="acteur_services__in")
    actions: Optional[List[int]] = Field(None, q="proposition_services__action_id__in")
    sous_categories: Optional[List[int]] = Field(
        None,
        q="proposition_services__sous_categories__id__in",
    )


@router.get("/sources", response=List[SourceSchema], summary="Liste des sources")
def sources(request):
    """
    Liste l'ensemble des <i>sources</i> possibles pour un acteur.
    """  # noqa
    qs = Source.objects.filter(afficher=True)
    return qs


@router.get(
    "/sous-categories",
    response=List[SousCategorieObjetSchema],
    summary="Liste des catégories d'objets",
)
def sous_categories(request):
    """
    Liste l'ensemble des <i>sous-catégories d'objet</i> possibles pour un acteur.
    """  # noqa
    qs = SousCategorieObjet.objects.filter(afficher=True)
    return qs


@router.get(
    "/actions", response=List[ActionSchema], summary="Liste des actions possibles"
)
def actions(request):
    """
    Liste l'ensemble des <i>actions</i> possibles sur un objet / déchet.
    """  # noqa
    qs = Action.objects.all()
    return qs


@router.get(
    "/actions/groupes",
    response=List[GroupeActionSchema],
    summary="Liste des groupes d'actions possibles",
)
def groupe_actions(request):
    """
    Liste l'ensemble des <i>actions</i> possibles sur un objet / déchet.
    """  # noqa
    qs = GroupeAction.objects.all()
    return qs


@router.get("/acteurs", response=List[ActeurSchema], summary="Liste des acteurs actifs")
@paginate
def acteurs(
    request,
    filters: ActeurFilterSchema = Query(...),
    latitude: float | None = None,
    longitude: float | None = None,
    rayon: int = 2,
):
    """
    Les acteurs correspondant à un point sur la carte Longue Vie Aux Objets

    Pour retrouver les acteurs à proximité :
    - Indiquer une latitude / longitude (exemple : latitude=48.86 et longitude=2.3)
    - Indiquer un rayon (optionnel) en km : les résultats en dehors de ce rayon ne seront pas retournés

    Si la latitude ou longitude sont manquantes, alors tous les résultats seront retournés triés par nom.
    """  # noqa
    qs = DisplayedActeur.objects.filter(
        statut=ActeurStatus.ACTIF,
    ).order_by("nom")
    qs = filters.filter(qs)

    if latitude and longitude:
        point = Point(longitude, latitude, srid=4326)
        qs = (
            qs.filter(
                location__dwithin=(
                    point,
                    distance_to_decimal_degrees(D(km=rayon), latitude),
                )
            )
            .annotate(distance=Distance("location", point))
            .order_by("distance")
        )

    return qs


@router.get(
    "/acteurs/types",
    response=List[ActeurTypeSchema],
    summary="Liste des actions possibles",
)
def acteurs_types(request):
    """
    Liste l'ensemble des <i>types</i> d'acteurs possibles.
    """  # noqa
    qs = ActeurType.objects.all()
    return qs


@router.get(
    "/acteurs/services",
    response=List[ActeurServiceSchema],
    summary="Liste des services proposés par les acteurs",
)
def services(request):
    """
    Liste l'ensemble des <i>services</i> qui peuvent être proposés par un acteur.
    """  # noqa
    qs = ActeurService.objects.all()
    return qs


@router.get(
    "/acteur",
    response=ActeurSchema,
    summary="Retrouver un acteur actif",
)
def acteur(request, identifiant_unique: str):
    return get_object_or_404(
        DisplayedActeur, pk=identifiant_unique, statut=ActeurStatus.ACTIF
    )


@router.get("/autocomplete/configurateur")
def autocomplete_epcis(request, query: str):
    return search_epci_code(query)
