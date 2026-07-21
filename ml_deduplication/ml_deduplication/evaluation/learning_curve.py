import logging

import numpy as np
import polars as pl

RANDOM_SEED = 42

logger = logging.getLogger(__name__)


def _sample_clusters_near_target(
    df_positives: pl.DataFrame,
    target_count: int,
    tolerance: int = 20,
    seed: int = RANDOM_SEED,
) -> list:
    """Sample cluster_ids so the total row count stays close to target_count.

    Works regardless of cluster size skew by iteratively adding or removing
    clusters after an initial random sample.
    """
    rng = np.random.RandomState(seed)

    # Pre-compute cluster sizes for fast lookup
    cluster_sizes = df_positives.group_by("cluster_id").len().to_dicts()
    size_map = {row["cluster_id"]: row["len"] for row in cluster_sizes}
    all_cluster_ids = list(size_map.keys())

    mean_size = np.mean(list(size_map.values()))
    estimated_num_clusters = max(1, int(target_count / mean_size))

    # Initial random sample
    current_ids = list(
        rng.choice(
            all_cluster_ids,
            size=min(estimated_num_clusters, len(all_cluster_ids)),
            replace=False,
        )
    )
    current_count = sum(size_map[cid] for cid in current_ids)
    remaining_ids = [cid for cid in all_cluster_ids if cid not in current_ids]

    # Iteratively adjust until within tolerance
    while abs(current_count - target_count) > tolerance:
        if current_count < target_count:
            if not remaining_ids:
                break
            next_cid = rng.choice(remaining_ids)
            current_ids.append(next_cid)
            remaining_ids.remove(next_cid)
            current_count += size_map[next_cid]
        else:
            if not current_ids:
                break
            remove_cid = rng.choice(current_ids)
            current_ids.remove(remove_cid)
            remaining_ids.append(remove_cid)
            current_count -= size_map[remove_cid]

    return current_ids


def generate_df_features_subset(
    df_features: pl.DataFrame, train_fraction: float
) -> pl.DataFrame:

    df_test = df_features.filter(pl.col("split") == "test")
    df_train = df_features.filter(pl.col("split") == "train")

    num_to_sample = int(train_fraction * len(df_train))
    target_positives = num_to_sample // 2

    df_train_positives = df_train.filter(
        (pl.col("label")) & (pl.col("cluster_id").is_not_null())
    )

    cluster_ids_to_keep = _sample_clusters_near_target(
        df_train_positives, target_positives
    )

    df_train_positives_kept = df_train_positives.filter(
        pl.col("cluster_id").is_in(cluster_ids_to_keep)
    )

    actual_positives = len(df_train_positives_kept)

    df_final = pl.concat(
        [
            df_train_positives_kept,
            df_train.filter(pl.col("label").not_()).sample(
                n=actual_positives,
                seed=RANDOM_SEED,
            ),
            df_test,
        ],
    )

    num_cluster_kept_in_train = (
        df_final.filter((pl.col("split") == "train") & pl.col("label"))
        .select(pl.col("cluster_id").n_unique())
        .item()
    )

    logger.debug("Number of true cluster kept in train : %s", num_cluster_kept_in_train)
    logger.debug(
        "Num labels in train : %s",
        df_final.filter((pl.col("split") == "train")).group_by("label").len(),
    )

    return df_final


def generate_learning_curve(
    df_features: pl.DataFrame,
    training_hyperparams: dict,
    train_sizes=[0.1, 0.33, 0.55, 0.78, 1.0],
) -> dict:
    pass


if __name__ == "__main__":
    df_features = pl.read_parquet("datasets/features_dataset_20260718.parquet")
    generate_df_features_subset(df_features, 0.1)
