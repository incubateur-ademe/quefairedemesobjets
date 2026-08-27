"""Module used to create the dataset of acteur pairs that will then used in training.
The dataset is created using different methods like manual annotation and random sampling.
"""

import argparse
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from ml_deduplication.dataset.clusters import (
    balance_entities_dataset,
    create_entities_df_from_manual_labeling,
    create_entities_df_from_ml_manual_labeling,
    create_entity_df_from_ml_inference_manual_labeling,
)
from ml_deduplication.dataset.pairs import (
    create_entity_pairs_from_database_random_sampling,
    create_entity_pairs_from_manual_labeling,
    create_entity_pairs_from_ml_inference_manual_labeling,
    create_entity_pairs_from_ml_manual_labeling,
)
from ml_deduplication.dataset.utils import balance_pairs_dataset

RANDOM_SEED = 42

logger = logging.getLogger(__name__)


def create_full_pair_dataset(
    datasets_path: Path,
    database_connection_uri: str,
    num_examples_per_class: int = 1000,
) -> pl.DataFrame:
    """Create the full balanced dataset for training.

    Orchestrates the creation of the dataset by calling functions to extract
    pairs from various sources (manual labeling, database changes, random sampling)
    and then balances the dataset.

    Parameters
    ----------
    datasets_path : Path
        Path to the directory containing the dataset CSV files.
    database_connection_uri : str
        URI for the database connection.

    Returns
    -------
    pl.DataFrame
        A balanced Polars DataFrame containing the final dataset of actor pairs
        with columns:
        - identifiant_unique_i: The first actor's unique identifier.
        - identifiant_unique_j: The second actor's unique identifier.
        - label: Boolean indicating if the pair is a match.
        - cluster_id: The hash of the cluster ID for positive pairs, null otherwise.
    """
    df_pairs_ml_manual_labeling = create_entity_pairs_from_ml_manual_labeling(
        datasets_path
    )

    df_pairs_manual_labeling = create_entity_pairs_from_manual_labeling(
        datasets_path / "false_positives_suggestions.csv",
        datasets_path / "true_negatives_suggestions.csv",
        datasets_path / "true_positives_suggestions.csv",
        database_connection_uri,
    )

    df_pairs_ml_inference_manual_labeling = (
        create_entity_pairs_from_ml_inference_manual_labeling(datasets_path)
    )

    df_pairs_database_random_sampling = (
        create_entity_pairs_from_database_random_sampling(database_connection_uri)
    )

    df_pairs_balanced = balance_pairs_dataset(
        df_pairs_ml_manual_labeling,
        df_pairs_manual_labeling,
        df_pairs_ml_inference_manual_labeling,
        df_pairs_database_random_sampling,
        num_examples_per_class,
    )

    return df_pairs_balanced


def create_full_entities_dataset(
    datasets_path: Path,
    database_connection_uri: str,
    num_examples_per_class: int = 1000,
) -> pl.DataFrame:
    """Create the full balanced dataset for training.

    Orchestrates the creation of the dataset by calling functions to extract
    pairs from various sources (manual labeling, database changes, random sampling)
    and then balances the dataset.

    Parameters
    ----------
    datasets_path : Path
        Path to the directory containing the dataset CSV files.
    database_connection_uri : str
        URI for the database connection.

    Returns
    -------
    pl.DataFrame
        A balanced Polars DataFrame containing the final dataset of actor pairs
        with columns:
        - identifiant_unique_i: The first actor's unique identifier.
        - identifiant_unique_j: The second actor's unique identifier.
        - label: Boolean indicating if the pair is a match.
        - cluster_id: The hash of the cluster ID for positive pairs, null otherwise.
    """
    df_entities_ml_manual_labeling = create_entities_df_from_ml_manual_labeling(
        datasets_path
    )

    df_entities_suggestions_manual_labeling = create_entities_df_from_manual_labeling(
        datasets_path / "false_positives_suggestions.csv",
        datasets_path / "true_negatives_suggestions.csv",
        datasets_path / "true_positives_suggestions.csv",
        database_connection_uri,
    )

    df_entities_ml_inference_manual_labeling = (
        create_entity_df_from_ml_inference_manual_labeling(datasets_path)
    )

    df_entities_balanced = balance_entities_dataset(
        df_entities_ml_manual_labeling,
        df_entities_suggestions_manual_labeling,
        df_entities_ml_inference_manual_labeling,
        database_connection_uri,
        num_examples_per_class,
    )

    return df_entities_balanced


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for dataset creation."""
    parser = argparse.ArgumentParser(
        description="Create a balanced dataset of actor pairs for ML training."
    )
    parser.add_argument(
        "--dataset-type",
        type=str,
        default="pairs",
        choices=["pairs", "entities"],
        help="Type of dataset to generate, either entity pairs dataset or simple entities dataset."
        "Defaults to pairs.",
    )
    parser.add_argument(
        "--datasets-path",
        type=Path,
        default=Path(os.environ.get("ML_DATASETS_PATH", "")),
        help="Path to the directory containing the dataset CSV files. "
        "Defaults to ML_DATASETS_PATH environment variable.",
    )
    parser.add_argument(
        "--database-uri",
        type=str,
        default=os.environ.get("DATABASE_CONNECTION_URI", ""),
        help="URI for the database connection. "
        "Defaults to DATABASE_CONNECTION_URI environment variable.",
    )
    parser.add_argument(
        "--dataset-output-path",
        type=Path,
        default=None,
        help="Path where the output parquet file will be saved. "
        "Defaults to <datasets-path>/ml_dataset_<date>.parquet.",
    )
    parser.add_argument(
        "--num-examples-per-class",
        type=int,
        default=1000,
        help="Target number of examples for each label (positive and negative). "
        "Default is 1000.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    args = parse_args()

    if not args.datasets_path:
        raise ValueError(
            "No datasets path provided. Use --datasets-path or set ML_DATASETS_PATH env var."
        )
    if not args.database_uri:
        raise ValueError(
            "No database URI provided. Use --database-uri or set DATABASE_CONNECTION_URI env var."
        )

    dataset_type = args.dataset_type
    if dataset_type == "pairs":
        df_dataset = create_full_pair_dataset(
            args.datasets_path,
            args.database_uri,
            args.num_examples_per_class,
        )
    elif dataset_type == "entities":
        df_dataset = create_full_entities_dataset(
            args.datasets_path,
            args.database_uri,
            args.num_examples_per_class,
        )
    else:
        raise ValueError(f"{dataset_type} not a valid choice")

    logger.info("Dataset generated with len: %s", len(df_dataset))
    output_path = (
        args.dataset_output_path
        if args.dataset_output_path
        else args.datasets_path
        / f"ml_dataset_{datetime.now(tz=timezone.utc):%Y%m%d}_{dataset_type}.parquet"
    )
    df_dataset.write_parquet(output_path)
    logger.info(f"Dataset written to {output_path}")
