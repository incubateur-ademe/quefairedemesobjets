"""
Tâche pour la gestion d'un cluster (parent + enfants),
utilise les sous tâches db_manage_parent et db_manage_child
"""

from django.db import transaction
from rich import print

from qfdmo.models.acteur import Acteur, RevisionActeur
from scripts.deduplication.models.acteur_map import ActeurMap
from scripts.deduplication.models.change import Change
from scripts.deduplication.tasks.db_manage_child import db_manage_child
from scripts.deduplication.tasks.db_manage_parent import db_manage_parent


def db_manage_cluster(
    cluster_id: str,
    identifiants_uniques: list[str],
    parent_ids_to_children_count_db: dict,
    sources_preferred_ids: list[int],
    is_dry_run: bool,
) -> list[Change]:
    """Fonction de gestion d'un cluster qui gère le parent et les enfants
    via des fonctions dédiées

    Args:
        db_engine (Engine): connexion à la DB
        cluster_id (str): Identifiant du cluster
        identifiants_uniques (list[str]): liste des IDs des acteurs du cluster
        parent_ids_to_children_count_db (dict): mapping parent_id -> nombre d'enfants
        sources_preferred_ids (list[int]): liste des IDs de sources préférées
        is_dry_run (bool): mode test ou non

    Returns:
        list[Change]: liste des changements effectués
    """
    print(f"\nGESTION DU CLUSTER {cluster_id=}")
    print("Récupération des données des acteurs")
    # On construit un dict avec l'identifiant_unique comme clef
    # et pour chaque acteur, on récupère les données des 3 tables
    acteurs_revision = RevisionActeur.objects.filter(pk__in=identifiants_uniques)
    acteurs_base = Acteur.objects.filter(pk__in=identifiants_uniques)
    print(f"{len(acteurs_revision)=}")
    print(f"{len(acteurs_base)=}")

    # Construction du dictionnaire acteurs avec ID comme clef
    # pour nous aider à gérer le cluster
    acteurs_maps = []
    for id in identifiants_uniques:
        acteurs_maps.append(
            ActeurMap(
                identifiant_unique=id,
                # .first() retourne soit l'object soit None, ce qui
                # est pratique pour les tests de présence et décider
                # si on doit créer des révisions plus tards
                table_states={
                    "revision": acteurs_revision.filter(pk=id).first(),
                    "base": acteurs_base.filter(pk=id).first(),
                },
                children_count=parent_ids_to_children_count_db.get(id, 0),
                is_parent=parent_ids_to_children_count_db.get(id, 0) > 0,
            )
        )
    print(acteurs_maps)

    changes = []

    with transaction.atomic():
        # --------------------------------------
        # GESTION PARENT
        # --------------------------------------
        parent_id, change = db_manage_parent(
            acteurs_maps, sources_preferred_ids, is_dry_run
        )
        changes.append(change)

        # --------------------------------------
        # GESTION DES ENFANTS
        # --------------------------------------
        # Tous les acteurs qui ne sont pas le parent sont des enfants
        children_maps = [x for x in acteurs_maps if x.identifiant_unique != parent_id]
        for child_map in children_maps:
            change = db_manage_child(child_map, parent_id, is_dry_run)
            changes.append(change)

    return changes
