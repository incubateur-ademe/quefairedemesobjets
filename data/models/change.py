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
"""

from pydantic import BaseModel

from qfdmo.models import RevisionActeur


class ChangeActeurUpdateParent(BaseModel):
    """Un acteur est rattaché à un parent,
    l'acteur peut avoir ou pas un parent existant"""

    identifiant_unique: str
    parent_id: str

    def apply(self):
        raise NotImplementedError("Revoir logique d'ensemble")
        # _ = RevisionActeur.objects.filter(identifiant_unique=self.identifiant_unique)
        # etc...


class ChangeActeurCreateAsParent(BaseModel):
    """Un parent est créé sur la base de
    données d'acteurs"""

    # L'identifiant unique peut être fournit
    # (ex: UUID à partir des ID des enfants)
    # et il sera utilisé, sinon on génère un
    identifiant_unique: str | None
    data: dict

    def apply(self) -> str:
        raise NotImplementedError("Revoir logique d'ensemble")
        # Si ID fournit, on vérifie qu'il n'existe pas
        rev = RevisionActeur.objects.filter(identifiant_unique=self.identifiant_unique)
        if rev.exists():
            raise ValueError(f"Acteur {self.identifiant_unique} déjà existant")

        rev = RevisionActeur(**self.data)
        rev.save()

        return rev.identifiant_unique


class ChangeActeurEnrichParent(BaseModel):
    identifiant_unique: str
    data: dict


class ChangeActeurDeleteAsParent(BaseModel):
    """Suppresion d'un acteur supposé parent"""

    identifiant_unique: str

    def apply(self):
        raise NotImplementedError("Revoir logique d'ensemble")
        # TODO: peut être déjà supprimé par https://github.com/incubateur-ademe/quefairedemesobjets/pull/1247
        # si oui condition inverse: il faut ordonner les changements de cluster
        # pour avoir les ChangeActeurUpdateParent en 1er et que l'observer
        # fasse le nettoyage avant qu'on arrive ici
        rev = RevisionActeur.objects.filter(identifiant_unique=self.identifiant_unique)
        if not rev.exists():
            raise ValueError(f"Acteur à supprimer {self.identifiant_unique} non trouvé")

        rev.delete()


TYPES_TO_MODELS = {
    "acteur_update_parent": ChangeActeurUpdateParent,
    "acteur_create_as_parent": ChangeActeurCreateAsParent,
    "acteur_delete_as_parent": ChangeActeurDeleteAsParent,
}
