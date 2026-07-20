import logging
from collections import defaultdict
from typing import Any

import polars as pl
from sklearn.model_selection import train_test_split

logging.getLogger(__name__)


def create_cluster_to_acteurs_dict(features_df: pl.DataFrame) -> dict[str, set[str]]:
    """Build a dict that map cluster_ids to list of acteur_id"""
    cluster_to_acteurs_dict = defaultdict(set)

    for row in features_df.iter_rows(named=True):
        cluster_id = row["cluster_id"]
        for suffix in ["_i", "_j"]:
            if row["label"]:
                cluster_to_acteurs_dict[cluster_id].add(
                    row[f"identifiant_unique{suffix}"]
                )
            else:
                id_ = row[f"identifiant_unique{suffix}"]
                cluster_id = f"singleton__{id_}"
                cluster_to_acteurs_dict[cluster_id].add(
                    row[f"identifiant_unique{suffix}"]
                )

    return cluster_to_acteurs_dict


def create_acteur_to_cluster_dict(
    cluster_to_acteurs_dict: dict[str, set[str]],
) -> dict[str, str]:
    """Build a dict mapping acteur_id to cluster_id from a cluster_to_acteurs_dict"""
    acteur_to_cluster_id = {}

    for cluster_id, acteur_id_list in cluster_to_acteurs_dict.items():
        for acteur_id in acteur_id_list:
            acteur_to_cluster_id[acteur_id] = cluster_id

    return acteur_to_cluster_id


def build_entities_dict(
    df_features: pl.DataFrame, features_names: list[str]
) -> dict[str, dict[str, Any]]:
    """
    Construit un dictionnaire {id_entité: {feature: valeur, ...}} unique
    à partir des colonnes _i / _j de chaque paire.
    """
    entities = {}
    for row in df_features.iter_rows(named=True):
        for suffix, id_col in (
            ("_i", "identifiant_unique_i"),
            ("_j", "identifiant_unique_j"),
        ):
            eid = row[id_col]
            if eid not in entities:
                entity = {}
                for feature_name in features_names:
                    value = row[f"{feature_name}{suffix}"]
                    if isinstance(value, int) or isinstance(value, float):
                        value = str(value)
                    entity[feature_name] = value

                entity["location"] = (
                    row[f"latitude{suffix}"],
                    row[f"longitude{suffix}"],
                )
                entities[eid] = entity

    return entities


def partition_to_dict(
    dedupe_partitions,
) -> dict:
    """
    Convertit la sortie de `deduper.partition()` en dict {id: cluster_id}.
    les cluster_id sont générés automatiquement.
    Les entités que dedupe n'a rattachées à aucun cluster (cas limite selon
    versions) sont explicitement placées dans un cluster singleton.
    """
    id_to_cluster = {}
    for cluster_idx, (ids, _scores) in enumerate(dedupe_partitions):
        for eid in ids:
            id_to_cluster[eid] = f"c_{cluster_idx}"

    return id_to_cluster


def partition_to_results_dict(dedupe_partitions) -> dict:
    """
    Convertit la sortie de `deduper.partition()` en dict contenant le cluster id et le score de confiance.
    les cluster_id sont générés automatiquement.
    Utile pour logger les résultats.
    """
    id_to_cluster = {}
    for cluster_idx, (ids, scores) in enumerate(dedupe_partitions):
        children = []
        for eid, score in zip(ids, scores):
            children.append(
                {
                    "acteur_id": eid,
                    "score": float(score),
                }
            )
        id_to_cluster[cluster_idx] = children

    return id_to_cluster


def split_train_dev(
    df_train_features: pl.DataFrame,
    dev_ratio: float = 0.2,
    seed: int = 42,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Split df_features into train dev sets for training and hyper-parameters tuning.
    The column cluster_id_split is used in order to ensure there is no cluster data
    leaking between train and dev sets
    """
    train_cluster_ids, dev_cluster_ids = train_test_split(
        df_train_features.select("cluster_id_split").unique("cluster_id_split"),
        test_size=dev_ratio,
        random_state=seed,
    )

    df_train_sub = df_train_features.filter(
        pl.col("cluster_id_split").is_in(
            train_cluster_ids.get_column("cluster_id_split").to_list()
        )
    )

    df_dev = df_train_features.filter(
        pl.col("cluster_id_split").is_in(
            dev_cluster_ids.get_column("cluster_id_split").to_list()
        )
    )

    return df_train_sub, df_dev


def stringify_params_list(
    params: dict,
) -> dict:
    params = params.copy()
    params["dedupe_variables_config"] = [
        str(e) for e in params["dedupe_variables_config"]
    ]

    return params
