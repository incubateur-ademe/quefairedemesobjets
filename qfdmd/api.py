from ninja import ModelSchema, Router

from qfdmo.models.categorie_objet import SousCategorieObjet
from .models import Produit

router = Router()


class SousCategorieSchema(ModelSchema):
    url_carte: str

    class Meta:
        model = SousCategorieObjet
        fields = ["id"]


@router.get("/afficher_carte", response=SousCategorieSchema)
def afficher_carte(request, id: int):
    try:
        return (
            Produit.objects.get(
                id=id,
            )
            .sous_categories.filter(afficher_carte=True)
            .first()
        )

    except (
        AttributeError,
        Produit.DoesNotExist,
    ):
        return None
