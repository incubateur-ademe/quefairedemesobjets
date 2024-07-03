from ninja import Router
from .models import Produit

router = Router()


@router.get("/afficher_carte")
def afficher_carte(request, id: int):
    try:
        return (
            Produit.objects.get(id=id)
            .sous_categories.filter(qfdmd_afficher_carte=True)
            .exists()
        )
    except Produit.DoesNotExist:
        return None
