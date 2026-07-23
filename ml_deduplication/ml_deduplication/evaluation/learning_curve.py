import argparse
from datetime import datetime
import logging
import json
from pathlib import Path


import numpy as np
import polars as pl
import plotly.graph_objects as go

from tqdm import tqdm
from tqdm.contrib.logging import tqdm_logging_redirect

from ml_deduplication.training.training_pipeline import run_training_pipeline
from ml_deduplication.training.features import (
    DEDUPE_VARIABLES_CONFIG_FULL,
    FEATURES_NAMES_FROM_DATASET,
)

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

    if train_fraction == 1.0:
        return df_features

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


def generate_plotly_graph(trainings_results: list[dict]) -> go.Figure:

    training_sizes = []
    training_pairwise_precision_list = []
    training_pairwise_recall_list = []
    training_b3_precision_list = []
    training_b3_recall_list = []
    for res in trainings_results:
        train_size = res["train_size"]
        pairwise_metrics = res["metrics"]["pairwise"]
        cluster_metrics = res["metrics"]["clusterwise"]

        training_sizes.append(train_size)
        training_pairwise_precision_list.append(pairwise_metrics["precision"])
        training_pairwise_recall_list.append(pairwise_metrics["recall"])
        training_b3_precision_list.append(cluster_metrics["bcubed"]["precision"])
        training_b3_recall_list.append(cluster_metrics["bcubed"]["recall"])

    configs = [
        {
            "name": "Pairwise precision",
            "x": training_sizes,
            "y": training_pairwise_precision_list,
        },
        {
            "name": "Pairwise recall",
            "x": training_sizes,
            "y": training_pairwise_recall_list,
        },
        {
            "name": "Bcubed precision",
            "x": training_sizes,
            "y": training_b3_precision_list,
        },
        {"name": "Bcubed recall", "x": training_sizes, "y": training_b3_recall_list},
    ]

    lines = []

    for config in configs:
        line = go.Scatter(
            x=config["x"],
            y=config["y"],
            texttemplate="%{y:.3f}",
            textposition="top center",
            name=config["name"],
            mode="lines+markers+text",
        )
        lines.append(line)

    fig = go.Figure(lines)
    fig.update_yaxes(range=[0, 1.1], showgrid=True)
    fig.update_xaxes(title="Nombre d'observations dans le jeu d’entraînement")
    fig.update_layout(
        template="simple_white",
        title=f"Courbe d'apprentissage du {datetime.now():%d/%m/%Y}",
        height=720,
        width=1280,
    )

    return fig


def generate_learning_curve(
    df_features: pl.DataFrame,
    training_hyperparams: dict,
    train_fractions=[0.1, 0.25, 0.33, 0.50, 0.66, 0.75, 1.0],
) -> tuple[list[dict], go.Figure]:

    results = []

    with tqdm_logging_redirect():
        with tqdm(total=len(train_fractions)) as t:
            for train_fraction in train_fractions:
                logger.debug(
                    "------ Running training with %s%% of the dataset ------",
                    train_fraction * 100,
                )
                t.set_description(
                    "Training with %s%% of the dataset." % (train_fraction * 100)
                )

                df_features_sub = generate_df_features_subset(
                    df_features, train_fraction
                )
                _model, training_results, _ = run_training_pipeline(
                    df_features_sub, training_hyperparams
                )

                results.append(
                    {
                        "train_size": train_fraction
                        * len(df_features.filter(pl.col("split") == "train")),
                        "metrics": training_results["test_results"],
                    }
                )
                t.update()

    fig = generate_plotly_graph(results)
    return results, fig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a learning curve for the ML deduplication pipeline."
    )
    parser.add_argument(
        "dataset_path",
        type=Path,
        help="Path to the features dataset (.parquet file).",
    )
    parser.add_argument(
        "output_path",
        type=Path,
        help="Directory path to save the results JSON and HTML plot.",
    )
    parser.add_argument(
        "--fractions",
        type=float,
        nargs="+",
        default=[0.1, 0.25, 0.33, 0.50, 0.66, 0.75, 1.0],
        help="List of training fractions to evaluate (default: 0.1 0.25 0.33 0.50 0.66 0.75 1.0).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)

    args = parse_args()

    df_features = pl.read_parquet(args.dataset_path)
    training_hyperparams = {
        "index_predicates": False,
        "dedupe_variables_config": DEDUPE_VARIABLES_CONFIG_FULL,
        "features_names": FEATURES_NAMES_FROM_DATASET,
    }
    results, fig = generate_learning_curve(
        df_features, training_hyperparams, args.fractions
    )

    timestamp = datetime.now().strftime("%Y%m%dT%H%M")

    with open(args.output_path / f"learning_curve_results_{timestamp}.json", "w") as f:
        json.dump(results, f)
    fig.write_html(args.output_path / f"learning_curve_{timestamp}.html")
