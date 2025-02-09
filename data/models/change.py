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
 🔴 incovénient: les suggestions en DB deviennent dépendentes
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

# -----------------------------
# COLONNES
# -----------------------------
# Colonnes utilisées pour définir les changements
COL_CHANGE_TYPE = "change_type"  # = description + lien vers modèles
COL_CHANGE_ORDER = "change_order"  # = ordre d'application
COL_CHANGE_REASON = "change_reason"  # = debug

# -----------------------------
# 1) change_type
# -----------------------------
# Liste des changements possibles, l'avantage
# de définir des noms est de restreindre et d'expliciter
# au maximum les conséquences des changements (on pourrait
# utiliser 1 seul modèle totallement abstrait mais en traçabilité
# et ça deviendrait vite difficile à maintenir)
CHANGE_ACTEUR_PARENT_DELETE = "acteur_parent_delete"
CHANGE_ACTEUR_PARENT_KEEP = "acteur_parent_keep"
CHANGE_ACTEUR_POINT_TO_PARENT = "acteur_point_to_parent"
CHANGE_ACTEUR_CREATE_AS_PARENT = "acteur_create_as_parent"


# -----------------------------
# 2) Modèles pydantic
# -----------------------------
# Pour gérer les changements, en utilisant
# l'héritage selon les besoins


class ChangeActeur(BaseModel):
    """Modèle de base pour les changements d'un acteur'"""

    # On a besoin de savoir quel acteur changer
    identifiant_unique: str
    # Et quelle donnée changer (si c'est une update)
    data: dict = {}

    def data_validate(self):
        # Validation à définir au cas par cas
        raise NotImplementedError("Méthode à implémenter")

    def apply(self):
        # Modification à définir au cas par cas
        raise NotImplementedError("Méthode à implémenter")


class ChangeActeurUpdateData(ChangeActeur):
    """Modèle de mise à jour d'un acteur"""

    def apply(self):
        self.data_validate()
        rev = RevisionActeur.objects.get(identifiant_unique=self.identifiant_unique)
        for key, value in self.data.items():
            setattr(rev, key, value)
        rev.save()


class ChangeActeurCreateRevision(ChangeActeur):
    """Création de la révision d'un acteur"""

    def data_validate(self):
        pass

    def apply(self):
        self.data_validate()
        rev = RevisionActeur(**self.data)
        rev.save()


class ChangeActeurDeleteRevision(ChangeActeur):
    """Suppresion d'un acteur supposé parent"""

    def data_validate(self):
        pass

    def apply(self):
        self.data_validate()
        # Rien à faire, le parent doit être supprimé automatiquement
        # par les observers enfants
        pass


class ChangeActeurPointToParent(ChangeActeurUpdateData):
    """🔀 Pour pointer un acteur vers un parent,
    on MAJ sa data, donc on part du modèle d'update
    et on ajoute juste une validtion sur data"""

    def data_validate(self):
        # Si on doit rediriger un acteur vers un parent
        # alors on s'attend à ce que le parent existe
        parent = RevisionActeur.objects.filter(
            identifiant_unique=self.data["parent_id"]
        )
        if not parent.exists():
            raise ValueError(f"Parent {self.data['parent_id']} non trouvé")


class ChangeActeurCreateAsParent(ChangeActeurCreateRevision):
    """➕ Pour la création d'un parent, on créer une révision,
    donc on part du modèle de révision et on ajoute juste
    une validation data"""

    def data_validate(self):
        # Si le parent est a créer, alors on s'attend à ce qu'il n'existe pas
        rev = RevisionActeur.objects.filter(identifiant_unique=self.identifiant_unique)
        if rev.exists():
            raise ValueError(f"Parent à créer {self.identifiant_unique} déjà existant")


class ChangeActeurParentKeep(ChangeActeurUpdateData):
    """🟢 Pour la MAJ d'un parent existant, on le met à jour
    comme on MAJ un acteur mais avec la data qui nous intéresse"""

    def data_validate(self):
        # On fait confiance à la donnée qu'on reçoit,
        # on laisse les modèles Django se plaindre si pas content
        # MAIS on vérifie juste qu'on ne vient pas donner de source
        # à un parent
        if "source" in self.data or "source_id" in self.data:
            raise ValueError("Pas de source pour un parent")


class ChangeActeurParentDelete(ChangeActeurDeleteRevision):
    """🔴 Pour la suppression d'un parent, on supprime sa révision,
    donc on part du modèle de revision et on ajoute juste
    une validation data"""

    def data_validate(self):
        # Si notre logique de suppression automatique
        # des parents sans enfants fonctionne, alors
        # quand on arrive ici, le parent doit avoir été supprimé
        # par les observers
        rev = RevisionActeur.objects.filter(identifiant_unique=self.identifiant_unique)
        if rev.exists():
            raise ValueError(
                f"Parent {self.identifiant_unique} devrait déjà être supprimé"
            )


# -----------------------------
# 3) Mapping change_type ➡️ modèle
# -----------------------------
MAPPING_TYPES_TO_MODELS = {
    # -----------------------------
    # Changements de type clustering/déduplication
    # -----------------------------
    CHANGE_ACTEUR_POINT_TO_PARENT: ChangeActeurPointToParent,
    CHANGE_ACTEUR_CREATE_AS_PARENT: ChangeActeurCreateAsParent,
    CHANGE_ACTEUR_PARENT_KEEP: ChangeActeurParentKeep,
    CHANGE_ACTEUR_PARENT_DELETE: ChangeActeurParentDelete,
}
