from typing import List
from django.shortcuts import get_object_or_404
from ninja import ModelSchema, Router
from ninja.pagination import paginate

from qfdmo.models import ActeurStatus, DisplayedActeur

router = Router()


class ActeurSchema(ModelSchema):
    class Meta:
        model = DisplayedActeur
        fields = ["nom", "nom_commercial"]


@router.get("/acteurs", response=List[ActeurSchema], summary="Liste des acteurs actifs")
@paginate
def acteurs(request):
    return DisplayedActeur.objects.filter(
        statut=ActeurStatus.ACTIF,
    )


@router.get(
    "/acteur",
    response=ActeurSchema,
    summary="Retrouver un acteur actif",
)
def acteur(request, identifiant_unique: str):
    return get_object_or_404(DisplayedActeur, pk=id, statut=ActeurStatus.ACTIF)
