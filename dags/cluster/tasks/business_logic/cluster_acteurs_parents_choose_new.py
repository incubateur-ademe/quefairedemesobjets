import json
import uuid
from logging import getLogger

import numpy as np
import pandas as pd
from cluster.config.constants import COL_PARENT_ID_BEFORE
from cluster.tasks.business_logic.misc.df_sort import df_sort
from utils.django import django_setup_full

from data.models.change import (
    COL_CHANGE_MODEL_NAME,
    COL_CHANGE_ORDER,
    COL_CHANGE_REASON,
)
from data.models.changes import (
    ChangeActeurCreateAsParent,
    ChangeActeurDeleteAsParent,
    ChangeActeurKeepAsParent,
    ChangeActeurUpdateParentId,
    ChangeActeurVerifyRevision,
)

django_setup_full()

logger = getLogger(__name__)

REASON_ONE_PARENT_KEPT = "1️⃣ 1 seul parent existant → à garder"
REASON_PARENTS_KEEP_MOST_CHILDREN = "🎖️ 2+ parents → celui avec + d'enfants → à garder"
REASON_NO_PARENT_CREATE_ONE = "➕ Pas de parent → à créer"
REASON_POINT_TO_NEW_PARENT = "🔀 A pointer vers nouveau parent"
REASON_ALREADY_POINT_TO_PARENT = "🟰 Pointe déjà vers nouveau parent"
REASON_PARENT_TO_DELETE = "🔴 2+ parents → non choisi → à supprimer"


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


def cluster_acteurs_one_cluster_parent_changes_mark(
    df_one_cluster: pd.DataFrame,
    parent_id: str,
    change_model_name: str,
    parent_change_reason: str,
) -> pd.DataFrame:
    """Mark all changes from having selected a parent on 1 cluster.
    - apply changes on the parent itself
    - if children already pointing to parent -> no changes
    - if children not pointing to parent -> point to new parent
    - if orphan -> point to new parent
    """
    df = df_one_cluster.copy()

    parent_index = df[df["identifiant_unique"] == parent_id].index[0]
    if parent_index is None:
        raise ValueError(f"Parent non trouvé: {parent_id=}")

    # La première étape est de s'assurer que le nouveau parent
    # est bien en place
    df.loc[parent_index, COL_CHANGE_MODEL_NAME] = change_model_name
    df.loc[parent_index, COL_CHANGE_REASON] = parent_change_reason
    df.loc[parent_index, COL_CHANGE_ORDER] = 1

    # Ensuite tous les enfants (non-parents) doivent pointer vers le nouveau parent
    filter_point = (df["est_parent"] == False) & (  # noqa: E712
        df["identifiant_unique"] != parent_id
    )
    df[COL_PARENT_ID_BEFORE] = df["parent_id"]  # Pour debug
    df.loc[filter_point, "parent_id"] = parent_id
    df.loc[filter_point, COL_CHANGE_MODEL_NAME] = ChangeActeurUpdateParentId.name()
    df.loc[filter_point, COL_CHANGE_REASON] = REASON_POINT_TO_NEW_PARENT
    df.loc[filter_point, COL_CHANGE_ORDER] = 2

    # On identifie le cas particulier des enfants qui
    # pointent déjà vers le parent pour lesquels on a rien à changer
    filter_unchanged = df[
        df["parent_id"].notnull() & (df["parent_id"] == df[COL_PARENT_ID_BEFORE])
    ].index
    df.loc[filter_unchanged, COL_CHANGE_MODEL_NAME] = ChangeActeurVerifyRevision.name()
    df.loc[filter_unchanged, COL_CHANGE_REASON] = REASON_ALREADY_POINT_TO_PARENT
    df.loc[filter_unchanged, COL_CHANGE_ORDER] = 2

    # Enfin tous les anciens parents (si il y en a) doivent être supprimés
    filter_delete = (df["est_parent"] == True) & (  # noqa: E712
        df["identifiant_unique"] != parent_id
    )
    df.loc[filter_delete, COL_CHANGE_MODEL_NAME] = ChangeActeurDeleteAsParent.name()
    df.loc[filter_delete, COL_CHANGE_REASON] = REASON_PARENT_TO_DELETE
    df.loc[filter_delete, COL_CHANGE_ORDER] = 3

    return df


def cluster_acteurs_one_cluster_parent_choose(df: pd.DataFrame) -> tuple[str, str, str]:
    """Generate the decision on the parent selection for 1 cluster"""
    from qfdmo.models.acteur import ActeurStatus

    try:
        parents_count = df[df["est_parent"] == True][  # noqa: E712
            "identifiant_unique"
        ].nunique()

        if parents_count == 1:
            # Case: 1 parent = we keep it
            index = df[df["est_parent"] == True].index[0]  # noqa: E712
            parent_id = df.at[index, "identifiant_unique"]
            change_model_name = ChangeActeurKeepAsParent.name()
            change_reason = REASON_ONE_PARENT_KEPT

        elif parents_count >= 2:
            # Case: 2+ parents = we choose the parent with the most children
            # choose the parent with the most children among the active parents
            df_parents = df[df["est_parent"] == True]  # noqa: E712
            df_active_parents = df_parents[df_parents["statut"] == ActeurStatus.ACTIF]
            if df_active_parents.empty:
                df_active_parents = df_parents
            index = df_active_parents["nombre_enfants"].idxmax()
            parent_id = df_active_parents.at[index, "identifiant_unique"]
            change_model_name = ChangeActeurKeepAsParent.name()
            change_reason = REASON_PARENTS_KEEP_MOST_CHILDREN

        elif parents_count == 0:
            # Case: 0 parent = we create one
            ids_non_parents = df[df["est_parent"] == False][  # noqa: E712
                "identifiant_unique"
            ].tolist()
            parent_id = parent_id_generate(ids_non_parents)
            change_model_name = ChangeActeurCreateAsParent.name()
            change_reason = REASON_NO_PARENT_CREATE_ONE

        else:
            # Safety net if logic not refactored and we forget to handle a case
            raise ValueError(f"Cas non géré/logique mal pensée: {parents_count=}")

        return parent_id, change_model_name, change_reason
    except Exception as e:
        debug = json.dumps(df.to_dict(orient="records"), indent=2)
        logger.error(f"Problème cluster:\n{debug}")
        raise e


def cluster_acteurs_parents_choose_new(df_clusters: pd.DataFrame) -> pd.DataFrame:
    """Select and assign the new parents to a dataframe
    comprenant 1 ou plusieurs clusters.'"""

    from data.models.change import COL_CHANGE_ORDER

    dfs_marked = []

    df = df_clusters.copy()

    for cluster_id in df["cluster_id"].unique():

        # For each cluster we work on its filtered df
        df_cluster = df[df["cluster_id"] == cluster_id]

        # Decision on the new parent
        parent_id, change_model_name, change_reason = (
            cluster_acteurs_one_cluster_parent_choose(df_cluster)
        )
        # Si la décision est de créer un nouveau parent, alors
        # on ajoute 1 ligne à la df principale avec l'entrée
        # pour le nouveau parent (puis on récupère la df filtrée)
        if change_model_name == ChangeActeurCreateAsParent.name():
            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        [
                            {
                                "identifiant_unique": parent_id,
                                "parent_id": None,
                                "cluster_id": cluster_id,
                                "est_parent": True,
                                "nombre_enfants": 0,
                            }
                        ]
                    ),
                ],
                ignore_index=True,
            ).replace({np.nan: None})
            df_cluster = df[df["cluster_id"] == cluster_id]
        # Enfin on vient marquer les changements sur la df filtrée du cluster
        df_cluster_marked = cluster_acteurs_one_cluster_parent_changes_mark(
            df_cluster.copy(), parent_id, change_model_name, change_reason
        )
        dfs_marked.append(df_cluster_marked)

    # On reconstruit la df principale avec les changements marqués
    df = pd.concat(dfs_marked, ignore_index=True)
    df[COL_CHANGE_ORDER] = df[COL_CHANGE_ORDER].astype(int)
    return df_sort(df)
