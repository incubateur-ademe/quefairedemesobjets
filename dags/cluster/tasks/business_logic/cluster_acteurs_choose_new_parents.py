import uuid
from logging import getLogger

import pandas as pd
from rich import print
from utils.django import django_setup_full

django_setup_full()

from data.models.change import (  # noqa: E402
    CHANGE_ACTEUR_CREATE_AS_PARENT,
    CHANGE_ACTEUR_PARENT_DELETE,
    CHANGE_ACTEUR_PARENT_KEEP,
    CHANGE_ACTEUR_POINT_TO_PARENT,
    COL_CHANGE_ORDER,
    COL_CHANGE_REASON,
    COL_CHANGE_TYPE,
)

logger = getLogger(__name__)


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
    df = df_one_cluster

    # Validation d'entrée pour faciliter le stop/debug
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
    df.loc[filter_point, "parent_id"] = parent_id
    df.loc[filter_point, COL_CHANGE_TYPE] = CHANGE_ACTEUR_POINT_TO_PARENT
    df.loc[filter_point, COL_CHANGE_REASON] = "Pointe vers le nouveau parent"
    df.loc[filter_point, COL_CHANGE_ORDER] = 2

    # Enfin tous les anciens parents (si il y en a) doivent être supprimés
    filter_delete = (df["nombre_enfants"] > 0) & (df["identifiant_unique"] != parent_id)
    df.loc[filter_delete, COL_CHANGE_TYPE] = CHANGE_ACTEUR_PARENT_DELETE
    df.loc[filter_delete, COL_CHANGE_REASON] = "Parent non choisi -> supprimé"
    df.loc[filter_delete, COL_CHANGE_ORDER] = 3

    return df


def cluster_acteurs_one_cluster_parent_choose(df: pd.DataFrame) -> tuple[str, str, str]:
    """Décide de la sélection du parent sur 1 cluster"""

    parents_count = df[df["nombre_enfants"] > 0]["identifiant_unique"].nunique()

    if parents_count == 1:
        # Cas: 1 parent = on le garde
        index = df[df["nombre_enfants"] > 0].index[0]
        parent_id = df.at[index, "identifiant_unique"]
        change_type = CHANGE_ACTEUR_PARENT_KEEP
        change_reason = "1 seul parent existant -> on le garde"

    elif parents_count >= 2:
        # Cas: 2+ parents = on en choisit le parent avec le + d'enfants
        index = df["nombre_enfants"].idxmax()
        parent_id = df.at[index, "identifiant_unique"]
        change_type = CHANGE_ACTEUR_PARENT_KEEP
        change_reason = "2+ parents, on garde celui avec le + d'enfants"

    elif parents_count == 0:
        # Cas: 0 parent = on en crée un
        ids_non_parents = df[df["nombre_enfants"] == 0]["identifiant_unique"].tolist()
        parent_id = parent_id_generate(ids_non_parents)
        change_type = CHANGE_ACTEUR_CREATE_AS_PARENT
        change_reason = "Pas de parent existant -> on en crée un"

    else:
        # Safety net ou cas où la logique ci-dessus est mal refactorisée à l'avenir
        # et q'uon oublie de gérer un cas
        raise ValueError(f"Cas non géré/logique male pensée: {parents_count=}")

    return parent_id, change_type, change_reason


def cluster_acteurs_choose_new_parents(df_clusters: pd.DataFrame) -> pd.DataFrame:
    """Choisit et assigne les nouveaux parents d'une dataframe
    comprenant 1 ou plusieurs clusters.'"""

    # Pour stocker et reconstruire les nouveaux clusters
    dfs_marked = []

    df = df_clusters
    for cluster_id in df["cluster_id"].unique():

        # Pour chaque cluster on travaille sur sa df filtrée
        df_cluster = df[df["cluster_id"] == cluster_id]
        # Décision sur le nouveau parent
        parent_id, change_type, change_reason = (
            cluster_acteurs_one_cluster_parent_choose(df_cluster)
        )
        logger.info(
            f"Cluster {cluster_id=}: {parent_id=} {change_type=} {change_reason=}"
        )
        # Si la décision est de créer un nouveau parent, alors
        # on ajoute 1 ligne à la df principale avec l'entrée
        # pour le nouveau parent (puis on récupère la df filtrée)
        if change_type == CHANGE_ACTEUR_CREATE_AS_PARENT:
            print("inside CHANGE_ACTEUR_CREATE_AS_PARENT")
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
            )
            df_cluster = df[df["cluster_id"] == cluster_id]
        # Enfin on vient marquer les changements sur la df filtrée du cluster
        df_cluster_marked = cluster_acteurs_one_cluster_changes_mark(
            df_cluster, parent_id, change_type, change_reason
        )
        dfs_marked.append(df_cluster_marked)

    # On reconstruit la df principale avec les changements marqués
    df = pd.concat(dfs_marked, ignore_index=True)
    df[COL_CHANGE_ORDER] = df[COL_CHANGE_ORDER].astype(int)
    df = df.sort_values(
        by=["cluster_id", COL_CHANGE_ORDER, "identifiant_unique"], ascending=True
    )
    return df
