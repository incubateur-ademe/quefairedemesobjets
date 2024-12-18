"""
QUOI: Modèle de changement des acteurs

POURQUOI: vérifier que les changements sont conformes avant de les appliquer

COMMENT: la fonction db_manage_cluster retourne une liste de changements
qu'on peut comparer avec nos attentes

TODO: ceci est le début d'une architecture de suggestion:
 - le modèle serait renommé "Suggestion"
 - ces suggestions seraient stockées dans un table "acteur_suggestions"
 - et soit à la main soit automatisé (ML, auto-approve) on viendrait
 lire les suggestions et les faire jouer par une API
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class Change:
    operation: Literal[
        "parent_create",
        "parent_choose",
        "parent_delete",
        "child_create_revision",
        "child_update_revision",
    ]
    acteur_id: str
