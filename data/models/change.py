"""
💡 QUOI:
Modèles pydantic liés aux changements atomiques
apportés par les suggestions

🎯 POURQUOI:
 - pydantic nous permet de découpler les suggestions
   de la DB
 - mais la méthode .apply() nous permet d'utiliser
    les modèles qfdmo pour appliquer les changements
    au moment voulu

🚧 COMMENT APPLIQUER UN CHANGEMENT:
 - Faire passer la donner de suggestion dans le modèle
 - Appeler .apply()


🧊 MODELISATION DES SUGGESTIONS:
On pourrait stocker les changements des suggestions
sous forme modélisée:
 🟢 avantage: prêt a l'emploi (plus qu'a récupérer et faire apply
 au moment de l'approbation), mais au final gain marginal
 🔴 incovénient: les suggestions deviennent dépendentes
 des modèles, si les modèles changent on perd potentiellement
 les suggestions OU il faut en faire des migrations

Pour l'instant on voit que 🔴>>🟢 et on décide de:
 1) suggestion: on utilise le modèle UNIQUEMENT pour la validation,
    mais on stoque la donnée non modèlisée
 2) changement: on rejoue la donnée dans le modèle et on applique .apply()

Notes:
- Définir un modèle de changement dontles autres héritent
- Stocker l'ordre des changements par type
- Centralisation la résolution du template de la cellule changement dans l'admin dans
chaque modèle pydantic
 """

from pydantic import BaseModel

from qfdmo.models import RevisionActeur


class ChangeActeurUpdateParent(BaseModel):
    """Un acteur est rattaché à un parent,
    l'acteur peut avoir ou pas un parent existant"""

    id: str
    parent_id: str

    def apply(self):
        raise NotImplementedError("Revoir logique d'ensemble")
        # _ = RevisionActeur.objects.filter(id=self.id)
        # etc...


class ChangeActeurCreateAsParent(BaseModel):
    """Un parent est créé sur la base de
    données d'acteurs"""

    # L'identifiant unique peut être fournit
    # (ex: UUID à partir des ID des enfants)
    # et il sera utilisé, sinon on génère un
    id: str | None
    data: dict

    def apply(self) -> str:
        raise NotImplementedError("Revoir logique d'ensemble")
        # Si ID fournit, on vérifie qu'il n'existe pas
        rev = RevisionActeur.objects.filter(id=self.id)
        if rev.exists():
            raise ValueError(f"Acteur {self.id} déjà existant")

        rev = RevisionActeur(**self.data)
        rev.save()

        return rev.id


class ChangeActeurEnrichParent(BaseModel):
    id: str
    data: dict


class ChangeActeurDeleteAsParent(BaseModel):
    """Suppresion d'un acteur supposé parent"""

    id: str

    def apply(self):
        raise NotImplementedError("Revoir logique d'ensemble")
        # TODO: peut être déjà supprimé par https://github.com/incubateur-ademe/quefairedemesobjets/pull/1247
        # si oui condition inverse: il faut ordonner les changements de cluster
        # pour avoir les ChangeActeurUpdateParent en 1er et que l'observer
        # fasse le nettoyage avant qu'on arrive ici
        rev = RevisionActeur.objects.filter(id=self.id)
        if not rev.exists():
            raise ValueError(f"Acteur à supprimer {self.id} non trouvé")

        rev.delete()


TYPES_TO_MODELS = {
    "acteur_update_parent": ChangeActeurUpdateParent,
    "acteur_create_as_parent": ChangeActeurCreateAsParent,
    "acteur_delete_as_parent": ChangeActeurDeleteAsParent,
}
