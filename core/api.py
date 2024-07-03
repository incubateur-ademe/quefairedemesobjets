from typing import List
from ninja import NinjaAPI, ModelSchema
from qfdmo.models.categorie_objet import SousCategorieObjet

api = NinjaAPI()


class SousCategorieObjetSchema(ModelSchema):
    class Meta:
        model = SousCategorieObjet
        fields = ["id", "qfdmd_produits"]


@api.get("/sous_categories", response=List[SousCategorieObjetSchema])
def list_qfdmd_products(_):
    return SousCategorieObjet.objects.filter(qfdmd_afficher_carte=True)
