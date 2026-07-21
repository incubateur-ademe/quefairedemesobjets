"""Module that allows to create features from dataset ids, also does train/test split."""

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
    ml_dataset_filepath: Path, database_connection_uri: str
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

    df_features_preprocessed = add_train_test_split(df_features_preprocessed)

    with psycopg.connect(database_connection_uri) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE luis._ml_dataset_tmp")
            conn.commit()

    return df_features_preprocessed


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    ml_dataset_path = Path(os.environ["ML_DATASET_FILEPATH"])
    database_connection_uri = os.environ["DATABASE_CONNECTION_URI"]
    df_pairs = create_features_dataset(ml_dataset_path, database_connection_uri)
    df_pairs.write_parquet(
        ml_dataset_path.parent / f"features_dataset_{datetime.now():%Y%m%d}.parquet"
    )
