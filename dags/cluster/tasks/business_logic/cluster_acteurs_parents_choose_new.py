import json
import uuid
from logging import getLogger

import numpy as np
import pandas as pd
from utils.django import django_setup_full

from data.models.change import (
    CHANGE_ACTEUR_CREATE_AS_PARENT,
    CHANGE_ACTEUR_NOTHING_TO_DO,
    CHANGE_ACTEUR_PARENT_DELETE,
    CHANGE_ACTEUR_PARENT_KEEP,
    CHANGE_ACTEUR_POINT_TO_PARENT,
    COL_CHANGE_ORDER,
    COL_CHANGE_REASON,
    COL_CHANGE_TYPE,
)

django_setup_full()

logger = getLogger(__name__)

REASON_ONE_PARENT_KEPT = "1️⃣ 1 seul parent existant -> à garder"
REASON_PARENTS_KEEP_MOST_CHILDREN = "🎖️ 2+ parents -> celui avec + d'enfants -> à garder"
REASON_NO_PARENT_CREATE_ONE = "➕ Pas de parent -> à créer"
REASON_POINT_TO_NEW_PARENT = "🔀 A pointer vers nouveau parent"
REASON_ALREADY_POINT_TO_PARENT = "🟰 Pointe déjà vers nouveau parent"
REASON_PARENT_TO_DELETE = "🔴 2+ parents -> non choisi -> à supprimer"


def parent_id_generate(ids: list[str]) -> str:
    """
    Génère un UUID (pour l'identifiant_unique parent) à partir
    de la liste des identifiants des enfants du cluster.
    Le UUID généré doit être:
    - déterministe (même entrée donne même sortie)
    - ordre-insensible (sort automatique)

    Args:
        ids: liste des identifiants uniques des enfants

    Returns:
        str: nouvel identifiant_unique du parent
    """
    combined = ",".join(sorted(ids))
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, combined))


def cluster_acteurs_one_cluster_changes_mark(
    df_one_cluster: pd.DataFrame,
    parent_id: str,
    change_type: str,
    parent_change_reason: str,
) -> pd.DataFrame:
    """Marque les changements liés à 1 seul cluster:
     - sélection du parent
     - pointage des enfants vers parents
     - suppression des parents non choisis

    Ne modifie aucun acteur, marque juste les changements.

    """
    df = df_one_cluster.copy()

    parent_index = df[df["identifiant_unique"] == parent_id].index[0]
    if parent_index is None:
        raise ValueError(f"Parent non trouvé: {parent_id=}")

    # La première étape est de s'assurer que le nouveau parent
    # est bien en place
    df.loc[parent_index, COL_CHANGE_TYPE] = change_type
    df.loc[parent_index, COL_CHANGE_REASON] = parent_change_reason
    df.loc[parent_index, COL_CHANGE_ORDER] = 1

    # Ensuite tous les enfants (non-parents) doivent pointer vers le nouveau parent
    filter_point = (df["nombre_enfants"] == 0) & (df["identifiant_unique"] != parent_id)
    df["parent_id_before"] = df["parent_id"]  # Pour debug
    df.loc[filter_point, "parent_id"] = parent_id
    df.loc[filter_point, COL_CHANGE_TYPE] = CHANGE_ACTEUR_POINT_TO_PARENT
    df.loc[filter_point, COL_CHANGE_REASON] = REASON_POINT_TO_NEW_PARENT
    df.loc[filter_point, COL_CHANGE_ORDER] = 2

    # On identifie le cas particulier des enfants qui
    # pointent déjà vers le parent pour lesquels on a rien à changer
    filter_unchanged = df[
        df["parent_id"].notnull() & (df["parent_id"] == df["parent_id_before"])
    ].index
    df.loc[filter_unchanged, COL_CHANGE_TYPE] = CHANGE_ACTEUR_NOTHING_TO_DO
    df.loc[filter_unchanged, COL_CHANGE_REASON] = REASON_ALREADY_POINT_TO_PARENT

    # Enfin tous les anciens parents (si il y en a) doivent être supprimés
    filter_delete = (df["nombre_enfants"] > 0) & (df["identifiant_unique"] != parent_id)
    df.loc[filter_delete, COL_CHANGE_TYPE] = CHANGE_ACTEUR_PARENT_DELETE
    df.loc[filter_delete, COL_CHANGE_REASON] = REASON_PARENT_TO_DELETE
    df.loc[filter_delete, COL_CHANGE_ORDER] = 3

    return df


def cluster_acteurs_one_cluster_parent_choose(df: pd.DataFrame) -> tuple[str, str, str]:
    """Décide de la sélection du parent sur 1 cluster"""

    from data.models.change import (  # noqa: E402
        CHANGE_ACTEUR_CREATE_AS_PARENT,
        CHANGE_ACTEUR_PARENT_KEEP,
    )

    try:
        parents_count = df[df["nombre_enfants"] > 0]["identifiant_unique"].nunique()

        if parents_count == 1:
            # Cas: 1 parent = on le garde
            index = df[df["nombre_enfants"] > 0].index[0]
            parent_id = df.at[index, "identifiant_unique"]
            change_type = CHANGE_ACTEUR_PARENT_KEEP
            change_reason = REASON_ONE_PARENT_KEPT

        elif parents_count >= 2:
            # Cas: 2+ parents = on en choisit le parent avec le + d'enfants
            index = df["nombre_enfants"].idxmax()
            parent_id = df.at[index, "identifiant_unique"]
            change_type = CHANGE_ACTEUR_PARENT_KEEP
            change_reason = REASON_PARENTS_KEEP_MOST_CHILDREN

        elif parents_count == 0:
            # Cas: 0 parent = on en crée un
            ids_non_parents = df[df["nombre_enfants"] == 0][
                "identifiant_unique"
            ].tolist()
            parent_id = parent_id_generate(ids_non_parents)
            change_type = CHANGE_ACTEUR_CREATE_AS_PARENT
            change_reason = REASON_NO_PARENT_CREATE_ONE

        else:
            # Safety net si logique mal refactorisée et q'uon oublie de gérer un cas
            raise ValueError(f"Cas non géré/logique male pensée: {parents_count=}")

        return parent_id, change_type, change_reason
    except Exception as e:
        debug = json.dumps(df.to_dict(orient="records"), indent=2)
        logger.error(f"Problème cluster:\n{debug}")
        raise e


def cluster_acteurs_parents_choose_new(df_clusters: pd.DataFrame) -> pd.DataFrame:
    """Choisit et assigne les nouveaux parents d'une dataframe
    comprenant 1 ou plusieurs clusters.'"""

    from data.models.change import CHANGE_ACTEUR_CREATE_AS_PARENT, COL_CHANGE_ORDER

    dfs_marked = []

    df = df_clusters.copy()
    for cluster_id in df["cluster_id"].unique():

        # Pour chaque cluster on travaille sur sa df filtrée
        df_cluster = df[df["cluster_id"] == cluster_id]
        # Décision sur le nouveau parent
        parent_id, change_type, change_reason = (
            cluster_acteurs_one_cluster_parent_choose(df_cluster)
        )
        # Si la décision est de créer un nouveau parent, alors
        # on ajoute 1 ligne à la df principale avec l'entrée
        # pour le nouveau parent (puis on récupère la df filtrée)
        if change_type == CHANGE_ACTEUR_CREATE_AS_PARENT:
            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        [
                            {
                                "identifiant_unique": parent_id,
                                "parent_id": None,
                                "cluster_id": cluster_id,
                                "nombre_enfants": 0,
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            ).replace({np.nan: None})
            df_cluster = df[df["cluster_id"] == cluster_id]
        # Enfin on vient marquer les changements sur la df filtrée du cluster
        df_cluster_marked = cluster_acteurs_one_cluster_changes_mark(
            df_cluster.copy(), parent_id, change_type, change_reason
        )
        dfs_marked.append(df_cluster_marked)

    # On reconstruit la df principale avec les changements marqués
    df = pd.concat(dfs_marked, ignore_index=True)
    df[COL_CHANGE_ORDER] = df[COL_CHANGE_ORDER].astype(int)
    df = df.sort_values(
        by=["cluster_id", COL_CHANGE_ORDER, "identifiant_unique"], ascending=True
    )
    return df


def clusters_to_parents_get(df_clusters: pd.DataFrame) -> dict[str, str]:
    """Retrieve the selected parents from given clusters"""
    df_parents = df_clusters[
        df_clusters[COL_CHANGE_TYPE].isin(
            [
                CHANGE_ACTEUR_PARENT_KEEP,
                CHANGE_ACTEUR_CREATE_AS_PARENT,
            ]
        )
    ]
    return df_parents.set_index("cluster_id")["identifiant_unique"].to_dict()


def clusters_to_children_and_orphans_get(
    df_clusters: pd.DataFrame,
) -> dict[str, list[str]]:
    """Retrieve the children and orphans from given clusters"""
    df_acteurs = df_clusters[
        # To construct a mutually exclusive list more robustly with
        # clusters_to_parents_get we just take the opposite rule,
        # since there are only 2 parents conditions (create, keep),
        # and many more children/orphans conditions, it's easier that way
        ~df_clusters[COL_CHANGE_TYPE].isin(
            [
                CHANGE_ACTEUR_PARENT_KEEP,
                CHANGE_ACTEUR_CREATE_AS_PARENT,
            ]
        )
    ]
    return df_acteurs.groupby("cluster_id")["identifiant_unique"].apply(list).to_dict()
