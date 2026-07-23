"""Module used to create the dataset of acteur pairs that will then used in training.
The dataset is created using different methods like manual annotation and random sampling.
"""

import argparse
import os
from datetime import datetime
from pathlib import Path

import polars as pl
import psycopg

from ml_deduplication.dataset.utils import get_sql_files_folder_path

RANDOM_SEED = 42


def create_entity_pairs_from_ml_manual_labeling(
    ml_manual_labeling_datasets_folder_path: Path,
) -> pl.DataFrame:
    """
    See original spreadsheet : https://docs.google.com/spreadsheets/d/1HltmT0Rhq-NXHaRJpDeqNEXXHO87iZMKTl7144iZaJ4/edit?gid=154092679#gid=154092679

    Create actors pairs from manual labeling of the old ML experience.

    Reads CSV files matching 'Clusterisation *.csv' from the given folder,
    processes them to extract pairs of actors, and assigns labels based on
    the 'Good ?' column. It also computes a hash for the cluster ID to
    preserve cluster information for positive pairs.

    Parameters
    ----------
    ml_manual_labeling_datasets_folder_path : Path
        Path to the folder containing the CSV files for manual labeling.

    Returns
    -------
    pl.DataFrame
        A Polars DataFrame containing pairs of actors with columns:
        - identifiant_unique_i: The first actor's unique identifier.
        - identifiant_unique_j: The second actor's unique identifier.
        - label: Boolean indicating if the pair is a match.
        - cluster_id: The hash of the cluster ID for positive pairs, null otherwise.
    """
    csv_files_to_load = ml_manual_labeling_datasets_folder_path.glob(
        "Clusterisation *.csv"
    )

    dfs = []
    for csv_filepath in csv_files_to_load:
        df = (
            pl.read_csv(csv_filepath).lazy().rename({"Good ? ": "Good ?"}, strict=False)
        )
        df = df.filter(
            pl.col("Good ?").is_in(["oui", "non"])
            & (pl.col("identifiant_unique") != pl.col("parent_existant").fill_null(""))
        )
        df_pairs = (
            df.join(df, on="cluster_id")
            .with_columns(
                pl.min_horizontal(
                    pl.col("identifiant_unique"), pl.col("identifiant_unique_right")
                ).alias("identifiant_unique_i"),
                pl.max_horizontal(
                    pl.col("identifiant_unique"), pl.col("identifiant_unique_right")
                ).alias("identifiant_unique_j"),
                (pl.col("Good ?") == "oui").alias("label"),
            )
            .filter(
                (pl.col("identifiant_unique_i") != pl.col("identifiant_unique_j"))
                & (
                    pl.col("cluster_id")
                    .cum_count()
                    .over(
                        ["cluster_id", "identifiant_unique_i", "identifiant_unique_j"]
                    )
                    == 1
                )
            )
            .select(
                ["identifiant_unique_i", "identifiant_unique_j", "label", "cluster_id"]
            )
        )

        df_cluster_ids = (
            df_pairs.filter(pl.col("label"))
            .group_by("cluster_id")
            .agg(
                pl.col("identifiant_unique_i")
                .list.concat(pl.col("identifiant_unique_j"))
                .list.explode(empty_as_null=True)
                .alias("ids")
            )
            .with_columns(
                pl.col("ids")
                .list.unique()
                .sort()
                .hash(RANDOM_SEED)
                .alias("cluster_id_hash")
            )
        )
        df_pairs_with_cluster_id = df_pairs.join(
            df_cluster_ids, on=["cluster_id"], validate="m:1", how="left"
        ).with_columns(
            pl.when(pl.col("label").not_())
            .then(None)
            .otherwise(pl.col("cluster_id_hash"))
            .alias("cluster_id_hash")
        )  # Keep cluster_id only on pairs that are true

        dfs.append(
            df_pairs_with_cluster_id.select(
                [
                    "identifiant_unique_i",
                    "identifiant_unique_j",
                    "label",
                    pl.col("cluster_id_hash").alias("cluster_id").cast(pl.String),
                ]
            )
        )

    df_pairs_concat = (
        pl.concat(dfs)
        .unique(["identifiant_unique_i", "identifiant_unique_j"])
        .sort(["identifiant_unique_i", "identifiant_unique_j"])
        .collect()
    )

    return df_pairs_concat


def create_entity_pairs_from_manual_labeling(
    false_positives_suggestions_dataset_path: Path,
    true_negatives_suggestions_dataset_path: Path,
    true_positives_suggestions_dataset_path: Path,
    database_connection_uri: str,
) -> pl.DataFrame:
    """Create actors pairs from manual labeling suggestions.

    Reads false positives, true negatives, and true positives from CSV files,
    writes them to a temporary database table, queries for pairs using a SQL
    script, and assigns appropriate labels and cluster IDs.

    Parameters
    ----------
    false_positives_suggestions_dataset_path : Path
        Path to the CSV file containing false positive suggestions.
    true_negatives_suggestions_dataset_path : Path
        Path to the CSV file containing true negative suggestions.
    true_positives_suggestions_dataset_path : Path
        Path to the CSV file containing true positive suggestions.
    database_connection_uri : str
        URI for the database connection.

    Returns
    -------
    pl.DataFrame
        A Polars DataFrame containing pairs of actors with columns:
        - identifiant_unique_i: The first actor's unique identifier.
        - identifiant_unique_j: The second actor's unique identifier.
        - label: Boolean indicating if the pair is a match.
        - cluster_id: The hash of the cluster ID for positive pairs, null otherwise.
    """
    pairs_sql_query = (
        (get_sql_files_folder_path() / "pairs_query.sql")
        .read_text()
        .format("luis._suggestions_tmp")
    )

    dfs = []

    configs = [
        {
            "suggestions_dataset_filepath": false_positives_suggestions_dataset_path,
            "label": False,
        },
        {
            "suggestions_dataset_filepath": true_negatives_suggestions_dataset_path,
            "label": False,
        },
        {
            "suggestions_dataset_filepath": true_positives_suggestions_dataset_path,
            "label": True,
        },
    ]
    for config in configs:
        df_suggestions = pl.read_csv(config["suggestions_dataset_filepath"])
        df_suggestions.write_database(
            "luis._suggestions_tmp",
            connection=database_connection_uri,
            if_table_exists="replace",
        )
        df_suggestions_pairs = pl.read_database_uri(
            pairs_sql_query,
            uri=database_connection_uri,
        )

        df_suggestions_pairs = df_suggestions_pairs.with_columns(
            pl.lit(config["label"]).alias("label")
        )
        if not config["label"]:
            df_suggestions_pairs = df_suggestions_pairs.with_columns(
                pl.lit(None).alias("cluster_id").cast(pl.String)
            )

        dfs.append(df_suggestions_pairs)

    with psycopg.connect(database_connection_uri) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE luis._suggestions_tmp")
            conn.commit()

    df_pairs = pl.concat(dfs)

    return df_pairs


def create_entity_pairs_from_database_parent_changes(
    database_connection_uri: str,
) -> pl.DataFrame:
    """Create actors pairs from database parent changes.

    Retrieves pairs of actors from the database that have undergone parent
    changes, marking them as negative pairs (label=False).

    Parameters
    ----------
    database_connection_uri : str
        URI for the database connection.

    Returns
    -------
    pl.DataFrame
        A Polars DataFrame containing negative pairs of actors with columns:
        - identifiant_unique_i: The first actor's unique identifier.
        - identifiant_unique_j: The second actor's unique identifier.
        - label: Always False, indicating a negative pair.
        - cluster_id: Always null, as these are negative pairs.
    """
    sql_query_folder = get_sql_files_folder_path()

    df_pairs = (
        pl.read_database_uri(
            query=(
                sql_query_folder / "negatives_pairs_via_parent_change.sql"
            ).read_text(),
            uri=database_connection_uri,
        )
        .with_columns(
            pl.lit(False).alias("label"),
            pl.lit(None).alias("cluster_id").cast(pl.String),
        )
        .select(["identifiant_unique_i", "identifiant_unique_j", "cluster_id", "label"])
    )

    return df_pairs


def create_entity_pairs_from_database_random_sampling(
    database_connection_uri: str,
) -> pl.DataFrame:
    """Create actors pairs from database random sampling.

    Retrieves both negative and positive pairs of actors from the database
    using random sampling methods.

    Parameters
    ----------
    database_connection_uri : str
        URI for the database connection.

    Returns
    -------
    pl.DataFrame
        A Polars DataFrame containing both positive and negative pairs of actors
        with columns:
        - identifiant_unique_i: The first actor's unique identifier.
        - identifiant_unique_j: The second actor's unique identifier.
        - label: Boolean indicating if the pair is a match.
        - cluster_id: The hash of the cluster ID for positive pairs, null otherwise.
    """
    sql_query_folder = get_sql_files_folder_path()
    configs = [
        {
            "query": (
                sql_query_folder / "negatives_pairs_via_random_sampling.sql"
            ).read_text(),
            "label": False,
        },
        {
            "query": (
                sql_query_folder / "positives_pairs_via_random_sampling.sql"
            ).read_text(),
            "label": True,
        },
    ]
    dfs = []
    for config in configs:
        col_exprs = [pl.lit(config["label"]).alias("label")]
        if not config["label"]:
            col_exprs.append(pl.lit(None).alias("cluster_id").cast(pl.String))

        df_pairs = (
            pl.read_database_uri(query=config["query"], uri=database_connection_uri)
            .with_columns(col_exprs)
            .select(
                ["identifiant_unique_i", "identifiant_unique_j", "cluster_id", "label"]
            )
        )

        dfs.append(df_pairs)

    final_df = pl.concat(dfs)

    return final_df


def balance_dataset(
    df_pairs_ml_manual_labeling: pl.DataFrame,
    df_pairs_manual_labeling: pl.DataFrame,
    df_pairs_database_via_parent_change: pl.DataFrame,
    df_pairs_database_random_sampling: pl.DataFrame,
    num_examples_for_each_label: int = 1000,
) -> pl.DataFrame:
    """Balance the dataset by combining pairs from different sources.

    Combines pairs from manual labeling and database sources, then samples
    from the random sampling dataset to achieve the desired number of examples
    for each label (positive and negative).

    Parameters
    ----------
    df_pairs_ml_manual_labeling : pl.DataFrame
        Pairs derived from the old ML manual labeling.
    df_pairs_manual_labeling : pl.DataFrame
        Pairs derived from the new manual labeling.
    df_pairs_database_via_parent_change : pl.DataFrame
        Negative pairs derived from database parent changes.
    df_pairs_database_random_sampling : pl.DataFrame
        Pairs derived from database random sampling.
    num_examples_for_each_label : int, optional
        Target number of examples for each label (positive and negative).
        Default is 1000.

    Returns
    -------
    pl.DataFrame
        A balanced Polars DataFrame containing pairs of actors with columns:
        - identifiant_unique_i: The first actor's unique identifier.
        - identifiant_unique_j: The second actor's unique identifier.
        - label: Boolean indicating if the pair is a match.
        - cluster_id: The hash of the cluster ID for positive pairs, null otherwise.
    """
    df_pairs = pl.concat(
        [
            df_pairs_ml_manual_labeling,
            df_pairs_database_via_parent_change,
            df_pairs_manual_labeling,
        ],
        how="diagonal",
    )

    mean_actors_by_cluster = (
        df_pairs_database_random_sampling.filter(pl.col("label"))
        .group_by("cluster_id")
        .len()
        .mean()["len"]
        .item()
    )

    df_pairs = pl.concat(
        [
            df_pairs,
            df_pairs_database_random_sampling.filter(pl.col("label").not_()).sample(
                n=(
                    num_examples_for_each_label
                    - len(df_pairs.filter(pl.col("label").not_()))
                ),
                seed=42,
            ),
            df_pairs_database_random_sampling.filter(pl.col("label")).filter(
                pl.col("cluster_id").is_in(
                    df_pairs_database_random_sampling.select(
                        pl.col("cluster_id").unique()
                    )
                    .sample(
                        n=round(
                            (
                                num_examples_for_each_label
                                - len(df_pairs.filter(pl.col("label")))
                            )
                            / mean_actors_by_cluster
                        ),  # En moyenne 2.1 paires par cluster
                        seed=42,
                    )
                    .get_column("cluster_id")
                    .to_list()
                )
            ),
        ],
        how="diagonal",
    )

    return df_pairs


def create_full_dataset(
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

    df_pairs_database_via_parent_change = (
        create_entity_pairs_from_database_parent_changes(database_connection_uri)
    )
    df_pairs_database_random_sampling = (
        create_entity_pairs_from_database_random_sampling(database_connection_uri)
    )

    df_pairs_balanced = balance_dataset(
        df_pairs_ml_manual_labeling,
        df_pairs_manual_labeling,
        df_pairs_database_via_parent_change,
        df_pairs_database_random_sampling,
        num_examples_per_class,
    )

    return df_pairs_balanced


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for dataset creation."""
    parser = argparse.ArgumentParser(
        description="Create a balanced dataset of actor pairs for ML training."
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
    args = parse_args()

    if not args.datasets_path:
        raise ValueError(
            "No datasets path provided. Use --datasets-path or set ML_DATASETS_PATH env var."
        )
    if not args.database_uri:
        raise ValueError(
            "No database URI provided. Use --database-uri or set DATABASE_CONNECTION_URI env var."
        )

    df_pairs = create_full_dataset(
        args.datasets_path,
        args.database_uri,
        args.num_examples_per_class,
    )

    output_path = (
        args.dataset_output_path
        if args.dataset_output_path
        else args.datasets_path / f"ml_dataset_{datetime.now():%Y%m%d}.parquet"
    )
    df_pairs.write_parquet(output_path)
    print(f"Dataset written to {output_path}")
