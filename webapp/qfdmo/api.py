import math
from typing import List, Optional

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.shortcuts import get_object_or_404
from ninja import Field, FilterSchema, ModelSchema, Query, Router, Schema
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
    RevisionActeur,
    Source,
    SousCategorieObjet,
    VueActeur,
)
from qfdmo.models.acteur import DisplayedPropositionService

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


class PropositionServiceSchema(ModelSchema):
    action: ActionSchema = Field(..., description="L'action proposée")
    sous_categories: List[SousCategorieObjetSchema] = Field(
        ...,
        alias="sous_categories.all",
        description="Les sous-catégories d'objet concernées par cette action",
    )

    class Meta:
        model = DisplayedPropositionService
        fields = ["id"]


class BaseActeurSchema(ModelSchema):
    latitude: float
    longitude: float
    services: List[ActeurServiceSchema] = Field(
        ...,
        alias="acteur_services.all",
        description="Les services proposés pour un acteur",
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
        # SQL-annotated distances are `Distance` objects (meters via `.m`),
        # while the carte's Python-side sorting sets a raw float.
        return getattr(obj.distance, "m", obj.distance)

    class Meta:
        model = DisplayedActeur
        fields = ["nom_commercial", "identifiant_unique", "siret"]


class ActeurSchema(BaseActeurSchema):
    actions: List[ActionSchema] = Field(
        ..., alias="acteur_actions", description="Les actions proposés pour un acteur"
    )


class CarteActeurSchema(BaseActeurSchema):
    propositions_services: List[PropositionServiceSchema] = Field(
        ...,
        alias="proposition_services.all",
        description=(
            "Les propositions de service de l'acteur : pour chaque action, "
            "les sous-catégories d'objet concernées"
        ),
    )


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
    List the possible <i>sources</i> for an actor.
    """
    qs = Source.objects.filter(afficher=True)
    return qs


@router.get(
    "/sous-categories",
    response=List[SousCategorieObjetSchema],
    summary="Liste des catégories d'objets",
)
def sous_categories(request):
    """
    List the possible <i>sub-categories of objects</i> for an actor.
    """
    qs = SousCategorieObjet.objects.filter(afficher=True)
    return qs


@router.get(
    "/actions", response=List[ActionSchema], summary="Liste des actions possibles"
)
def actions(request):
    """
    List the possible <i>actions</i> on an object / waste.
    """
    qs = Action.objects.all()
    return qs


@router.get(
    "/actions/groupes",
    response=List[GroupeActionSchema],
    summary="Liste des groupes d'actions possibles",
)
def groupe_actions(request):
    """
    List the possible <i>actions</i> on an object / waste.
    """
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
    The actors corresponding to a point on the "Que faire de mes objets et déchets" map.

    To find actors near a point:
    - provide a latitude / longitude (example: latitude=48.86 and longitude=2.3)
    - provide a radius (optional) in km: results outside this radius will not be
      returned

    If the latitude or longitude are missing, then all results will be returned sorted
    by name.
    """
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
    List the possible <i>types</i> of actors.
    """
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
    """
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


def _model_field_names(model_class, include_properties=True) -> list[str]:
    """Field names of a Django model, mirroring the behaviour of
    the data-platform's `django_model_fields_get` so Airflow DAGs
    can build their UI params from the API instead of the ORM.

    Always excluded: internals (pk) & ManyToMany
    """
    from django.db import models
    from django.utils.functional import cached_property

    excluded = ["pk"]

    fields = [
        x.name
        for x in model_class._meta.get_fields()
        # ManyToMany case causing massive performance issues (e.g. on "sources")
        if not isinstance(x, models.ManyToManyField)
    ]

    attributes = []
    if include_properties:
        for attr_name in dir(model_class):
            attr = getattr(model_class, attr_name, None)
            if isinstance(attr, (property, cached_property)):
                attributes.append(attr_name)

    return [x for x in fields + attributes if x not in excluded]


class ModelFieldsSchema(Schema):
    with_properties: List[str]
    db_only: List[str]


@router.get(
    "/acteurs/columns",
    response=dict[str, ModelFieldsSchema],
    summary="Champs des modèles acteurs",
)
def acteurs_columns(request):
    """
    Actor models columns.
    Used by the data-platform (Airflow) to build the DAGs parameters.
    """
    return {
        "vue_acteur": {
            "with_properties": _model_field_names(VueActeur),
            "db_only": _model_field_names(VueActeur, include_properties=False),
        },
        "revision_acteur": {
            "with_properties": _model_field_names(RevisionActeur),
            "db_only": _model_field_names(RevisionActeur, include_properties=False),
        },
    }
