from typing import List
import math
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from django.shortcuts import get_object_or_404
from ninja import ModelSchema, Router, Field
from ninja.pagination import paginate

from qfdmo.models import ActeurStatus, DisplayedActeur, ActeurService, Action

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


class ActionSchema(ModelSchema):
    class Meta:
        model = Action
        fields = ["id", "code", "libelle", "couleur"]


class ServiceSchema(ModelSchema):
    class Meta:
        model = ActeurService
        fields = ["id", "code", "libelle"]


class ActeurSchema(ModelSchema):
    latitude: float
    longitude: float
    distance: float = Field(..., alias="distance.m")
    services: List[str] = Field(..., alias="get_acteur_services")

    class Meta:
        model = DisplayedActeur
        fields = ["nom", "nom_commercial", "adresse", "identifiant_unique", "siret"]


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
    "/services", response=List[ServiceSchema], summary="Liste des services proposés"
)
def services(request):
    """
    Liste l'ensemble des <i>services</i> qui peuvent être proposés par un acteur.
    """  # noqa
    qs = Action.objects.all()
    return qs


@router.get("/acteurs", response=List[ActeurSchema], summary="Liste des acteurs actifs")
@paginate
def acteurs(request, latitude: float = None, longitude: float = None, rayon: int = 2):
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
    "/acteur",
    response=ActeurSchema,
    summary="Retrouver un acteur actif",
)
def acteur(request, identifiant_unique: str):
    return get_object_or_404(DisplayedActeur, pk=id, statut=ActeurStatus.ACTIF)
