"""
QUOI: Modèle pour nous aider a gérer les différents états des acteurs

POURQUOI: les acteurs sont fragmentés dans 3 tables:
 - qfdmo_displayedacteur: besoin métier pour des raisons de confiance
 - qfdmo_revisionacteur: besoin pour MAJ des données
 - qfdmo_acteur: besoin car certaines entées displayedacteur n'ont pas de révision

COMMENT: la fonction db_manage_cluster va chercher les données de chaque table
acteur et construit 1 ActeurMap par acteur. Par la suite il est plus facile
de gérer les différents cas de figure
"""

from dataclasses import dataclass
from typing import Dict, Literal

from django.db.models import Model


@dataclass
class ActeurMap:
    identifiant_unique: str

    # Un dict avec les différent objets Django pour chaque acteur
    table_states: Dict[Literal["base", "revision", "displayed"], Model]

    # Le nombre d'enfants pour chaque acteur pour éviter d'avoir
    # à faire des requêtes à chaque fois pour prendre une décision
    # si l'acteur doit devenir nouveau parent, être un parent supprimé...
    children_count: int
    is_parent: bool
