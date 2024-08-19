from django.shortcuts import get_object_or_404
from ninja import ModelSchema, Router

from qfdmo.models.categorie_objet import SousCategorieObjet

router = Router()


class SousCategorieSchema(ModelSchema):
    url_carte: str

    class Meta:
        model = SousCategorieObjet
        fields = ["id"]


@router.get("/produit", response=SousCategorieSchema)
def sous_categorie_from_product(request, id: str):
    # L'API Data Ademe retourne un identifiant de la forme 180_0, 180_1 etc
    # pour les synonymes du produit 180.
    # On retourne donc la même sous_catégorie pour tous les synonymes, celle-ci
    # correspondant à la partie avant l'underscore
    id = id.split("_")[0]
    return get_object_or_404(
        SousCategorieObjet, qfdmd_produits__id__in=[id], afficher_carte=True
    )
