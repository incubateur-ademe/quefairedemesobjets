from ninja import ModelSchema, Router

from qfdmo.models.categorie_objet import SousCategorieObjet
from .models import Produit

router = Router()


class SousCategorieSchema(ModelSchema):
    url_carte: str

    class Meta:
        model = SousCategorieObjet
        fields = ["id"]


@router.get("/produit", response=SousCategorieSchema)
def sous_categorie_from_product(request, id: str):
    try:
        # L'API Data Ademe retourne un identifiant de la forme 180_0, 180_1 etc
        # pour les synonymes du produit 180.
        # On retourne donc la même sous_catégorie pour tous les synonymes, celle-ci
        # correspondant à la partie avant l'underscore
        id = id.split("_")[0]
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
