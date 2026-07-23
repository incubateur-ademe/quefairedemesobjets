"""Module that allows to create features from dataset ids, also does train/test split."""

import argparse
import logging
import os
from datetime import datetime
from pathlib import Path

import polars as pl
import psycopg
from sklearn.model_selection import train_test_split

from ml_deduplication.dataset.utils import get_sql_files_folder_path

logging.basicConfig()
logger = logging.getLogger(__name__)

RANDOM_SEED = 42


def preprocess_features_dataset(df_features: pl.DataFrame) -> pl.DataFrame:

    # Processing of "__empty__"
    df_features_preprocessed = df_features.with_columns(
        pl.selectors.by_dtype(pl.String)
        .exclude("cluster_id")
        .str.strip_chars()
        .replace("__empty__", None)
        .replace("", None)
    )

    # Processing empty latitude/longitude
    df_features_preprocessed = df_features_preprocessed.with_columns(
        pl.selectors.contains("latitude", "longitude").fill_null(0)
    )

    # Processing out of range latitude/longitude
    df_features_preprocessed = df_features_preprocessed.with_columns(
        pl.selectors.starts_with("latitude").clip(-90.0, 90.0),
        pl.selectors.starts_with("longitude").clip(-180.0, 180.0),
    )

    return df_features_preprocessed


def add_train_test_split(
    df_features_preprocessed: pl.DataFrame, test_size: float = 0.2
) -> pl.DataFrame:
    df_features_preprocessed = df_features_preprocessed.with_columns(
        pl.coalesce(
            [
                "cluster_id",
                pl.concat_str(
                    "identifiant_unique_i", "identifiant_unique_j", separator="___"
                ),
            ]
        ).alias("cluster_id_split")
    )

    train_cluster_ids, test_cluster_ids = train_test_split(
        df_features_preprocessed.select("cluster_id_split").unique("cluster_id_split"),
        test_size=test_size,
        random_state=RANDOM_SEED,
    )

    df_features_preprocessed_split = (
        df_features_preprocessed.with_columns().with_columns(
            pl.when(
                pl.col("cluster_id_split").is_in(
                    train_cluster_ids.get_column("cluster_id_split").to_list()
                )
            )
            .then(pl.lit("train"))
            .when(
                pl.col("cluster_id_split").is_in(
                    test_cluster_ids.get_column("cluster_id_split").to_list()
                )
            )
            .then(pl.lit("test"))
            .otherwise(pl.lit("unknown"))
            .alias("split")
        )
    )

    return df_features_preprocessed_split


def create_features_dataset(
    ml_dataset_filepath: Path, database_connection_uri: str, test_size: float = 0.2
) -> pl.DataFrame:

    df_ml_dataset = pl.read_parquet(ml_dataset_filepath)

    logger.debug(
        "Writing ML dataset of shape %s to table luis._ml_dataset_tmp into database.",
        df_ml_dataset.shape,
    )
    df_ml_dataset.write_database(
        "luis._ml_dataset_tmp",
        connection=database_connection_uri,
        if_table_exists="replace",
    )
    sql_features_generation = (
        get_sql_files_folder_path() / "features_generation.sql"
    ).read_text()

    logger.debug("Creating features in database and loading it into dataframe.")
    df_features = pl.read_database_uri(
        sql_features_generation, uri=database_connection_uri
    )
    logger.debug("Successfully loaded features.")

    df_features_preprocessed = preprocess_features_dataset(df_features)

    df_features_preprocessed = add_train_test_split(df_features_preprocessed, test_size)

    with psycopg.connect(database_connection_uri) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE luis._ml_dataset_tmp")
            conn.commit()

    return df_features_preprocessed


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for features engineering."""
    parser = argparse.ArgumentParser(
        description="Create features from actor pairs dataset and perform train/test split."
    )
    parser.add_argument(
        "--ml-dataset-filepath",
        type=Path,
        default=Path(os.environ.get("ML_DATASET_FILEPATH", "")),
        help="Path to the input ML dataset parquet file. "
        "Defaults to ML_DATASET_FILEPATH environment variable.",
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
        help="Path where the output features parquet file will be saved. "
        "Defaults to <ml-dataset-filepath parent>/features_dataset_<date>.parquet.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Proportion of the dataset to include in the test split. Default is 0.2.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level. Default is INFO.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logger.setLevel(getattr(logging, args.log_level))

    if not args.ml_dataset_filepath:
        raise ValueError(
            "No ML dataset filepath provided. Use --ml-dataset-filepath or set ML_DATASET_FILEPATH env var."
        )
    if not args.database_uri:
        raise ValueError(
            "No database URI provided. Use --database-uri or set DATABASE_CONNECTION_URI env var."
        )

    df_features = create_features_dataset(
        args.ml_dataset_filepath,
        args.database_uri,
        test_size=args.test_size,
    )

    output_path = (
        args.dataset_output_path
        if args.dataset_output_path
        else args.ml_dataset_filepath.parent
        / f"features_dataset_{datetime.now():%Y%m%d}.parquet"
    )
    df_features.write_parquet(output_path)
    logger.info("Features dataset written to %s", output_path)
