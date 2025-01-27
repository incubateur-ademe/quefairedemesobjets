import uuid
from logging import getLogger

import pandas as pd

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
    parent_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, combined))
    print("parent_id_generate", f"{ids=}", f"{parent_id=}")
    return parent_id


def choose_new_parent_from_one_cluster(df: pd.DataFrame) -> pd.DataFrame:
    """Choisit et assigne un nouveau parent à un cluster"""

    fields_required = [
        "identifiant_unique",
        "is_parent_current",
        "children_count",
    ]
    for field in fields_required:
        if field not in df.columns:
            raise ValueError(f"Champ {field} manquant dans la df")

    # Placeholder pour le parent
    df["is_parent_new"] = False
    df["parent_id"] = None

    parents_current_count = df["is_parent_current"].sum()
    if parents_current_count == 1:
        # Cas: 1 parent = on le garde
        df.at[df["is_parent_current"].idxmax(), "is_parent_new"] = True
    elif parents_current_count >= 2:
        raise NotImplementedError("Cas où il y a plusieurs parents non géré")
    elif parents_current_count == 0:
        # Cas: 0 parent
        pass
    else:
        # Safety net ou cas où la logique ci-dessus est mal refactorisée à l'avenir
        raise ValueError(f"Cas non géré/logique male pensée: {parents_current_count=}")

    # On assigne parent_id sur tous les acteurs qui ne sont pas parent_new
    parent_id = df[df["is_parent_new"]]["identifiant_unique"].values[0]
    df.loc[~df["is_parent_new"], "parent_id"] = parent_id

    # ---------------------------------
    # Validation
    # ---------------------------------
    # 1 et 1 seul nouveau parent sélectionné
    parents_new_count = df["is_parent_new"].sum()
    if parents_new_count != 1:
        raise ValueError(f"Plus qu'1 parent sélectionné: {parents_new_count=}")
    # Tous les non-parents doivent avoir un parent_id
    parent_id_missing = df[df.loc[~df["is_parent_new"], "parent_id"].isnull()]
    if not parent_id_missing.empty:
        logger.critical(f"Erreur: {parent_id_missing=}")
        raise ValueError("Tous les non-parents doivent avoir un parent_id")
    # Le parent ne doit pas avoir de parent_id
    parent_id_present = df[df["is_parent_new"]]["parent_id"].notnull()
    if parent_id_present.any():
        raise ValueError("Le parent ne doit pas avoir de parent_id")

    return df


def cluster_acteurs_choose_new_parents(df_clusters: pd.DataFrame) -> pd.DataFrame:
    """Choisit et assigne les nouveaux parents des clusters"""

    df = df_clusters

    for cluster_id in df["cluster_id"].unique():
        df_cluster = df[df["cluster_id"] == cluster_id]
        choose_new_parent_from_one_cluster(df_cluster)

    return df
