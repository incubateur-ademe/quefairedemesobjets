"""
QUOI: Modèle pour nous aider a gérer les différents états des acteurs

POURQUOI: les acteurs sont fragmentés dans 2 tables:
 - qfdmo_revisionacteur: besoin pour MAJ des données
 - qfdmo_acteur: besoin car certaines entées acteur n'ont pas de révision

COMMENT: la fonction db_manage_cluster va chercher les données de chaque table
acteur et construit 1 ActeurMap par acteur. Par la suite il est plus facile
de gérer les différents cas de figure
"""

from dataclasses import dataclass
from typing import Literal

from qfdmo.models.acteur import Acteur, RevisionActeur


@dataclass
class ActeurMap:
    """Mapping pour 1 acteur"""

    identifiant_unique: str

    # Un dict avec les différent objets Django pour chaque acteur
    table_states: dict[Literal["base", "revision"], RevisionActeur | Acteur | None]

    # Le nombre d'enfants pour chaque acteur pour éviter d'avoir
    # à faire des requêtes à chaque fois pour prendre une décision
    # si l'acteur doit devenir nouveau parent, être un parent supprimé...
    children_count: int
    is_parent: bool
