import logging
import math
from pathlib import Path

import polars as pl
import psycopg

from ml_deduplication.dataset import RANDOM_SEED
from ml_deduplication.dataset.utils import get_sql_files_folder_path

logger = logging.getLogger(__name__)


def create_entities_df_from_ml_manual_labeling(
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
        - identifiant_unique: The first actor's unique identifier.
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
        df = df.filter(pl.col("Good ?").is_in(["oui", "non"]))

        df_cluster_ids = (
            df.filter(pl.col("Good ?") == "oui")
            .group_by("cluster_id")
            .agg(pl.col("identifiant_unique").alias("ids"))
            .with_columns(
                pl.col("ids")
                .list.unique()
                .sort()
                .hash(RANDOM_SEED)
                .alias("cluster_id_hash")
            )
        )
        df_with_cluster_id = df.join(
            df_cluster_ids, on=["cluster_id"], validate="m:1", how="left"
        )

        dfs.append(
            df_with_cluster_id.select(
                [
                    "identifiant_unique",
                    pl.col("cluster_id_hash").alias("cluster_id").cast(pl.String),
                ]
            )
        )

    df_concat = pl.concat(dfs).unique(["identifiant_unique"]).collect()

    return df_concat


def create_entity_df_from_ml_inference_manual_labeling(
    ml_inference_manual_labeling_datasets_folder_path: Path,
) -> pl.DataFrame:
    """
    See original spreadsheet : https://docs.google.com/spreadsheets/d/1vAG5OViTbVKMZFmdiYZioA2Sn9lN9r6yEeOmdY4ks24/edit?hl=fr&gid=647125517#gid=647125517

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
        - identifiant_unique: The actor's unique identifier.
        - cluster_id: The hash of the cluster ID for positive pairs, null otherwise.
    """
    csv_files_to_load_list = [
        {
            "filename": "inference_annotation_20260805.csv",
            "cluster_colname": "cluster_label",
        },
        {
            "filename": "inference_annotation_sample_50_20260805.csv",
            "cluster_colname": "cluster_label",
        },
        {
            "filename": "inference_annotation_sample_100_20260817.csv",
            "cluster_colname": "cluster_id",
        },
    ]

    dfs_to_concat = []

    for config in csv_files_to_load_list:
        cluster_colname = config["cluster_colname"]
        filepath = (
            ml_inference_manual_labeling_datasets_folder_path / config["filename"]
        )
        df = pl.read_csv(filepath, schema_overrides={cluster_colname: pl.String})

        if cluster_colname == "cluster_label":  # Old manual annotation style
            df = df.select(["identifiant_unique", "cluster_label", "Review"])
            df = df.filter(pl.col("Review").is_not_null())
            df_cluster_ids = (
                df.filter(pl.col("Review") != "Pas ok")
                .group_by("cluster_label")
                .agg(pl.concat_list("identifiant_unique").alias("ids"))
                .with_columns(
                    pl.col("ids")
                    .list.unique()
                    .sort()
                    .hash(RANDOM_SEED)
                    .alias("cluster_id")
                    .cast(pl.String)
                )
            )

            df_with_cluster_ids = (
                df.with_columns(
                    pl.when(pl.col("Review") == "Pas ok")
                    .then(None)
                    .otherwise("cluster_label")
                    .alias("cluster_label")
                )
                .join(df_cluster_ids, on="cluster_label", how="left")
                .select(
                    [
                        "identifiant_unique",
                        "cluster_id",
                    ]
                )
            )
            dfs_to_concat.append(df_with_cluster_ids)

        elif cluster_colname == "cluster_id":  # New annotation style
            df = df.select(
                ["identifiant_unique", cluster_colname, "review", "cluster_id_manual"]
            )
            df = df.filter(pl.col("review").is_not_null())

            df = df.with_columns(
                pl.when(pl.col("review") == "OK")
                .then("cluster_id")
                .when(pl.col("review") == "Partiellement ok")
                .then(pl.coalesce("cluster_id_manual", "cluster_id"))
                .otherwise(None)
                .alias("cluster_id")
            ).select("identifiant_unique", "cluster_id")

            dfs_to_concat.append(df)

    final_df = pl.concat(dfs_to_concat)
    return final_df.unique(["identifiant_unique"])


def create_entities_df_from_manual_labeling(
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
        - identifiant_unique: The first actor's unique identifier.
        - cluster_id: The hash of the cluster ID for positive pairs, null otherwise.
    """
    entities_sql_query = (
        (get_sql_files_folder_path() / "entities_from_suggestions.sql")
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

        if "true_candidate_filter" not in df_suggestions.columns:
            df_suggestions = df_suggestions.with_columns(
                pl.lit(None).alias("true_candidate_filter")
            )
        df_suggestions.write_database(
            "luis._suggestions_tmp",
            connection=database_connection_uri,
            if_table_exists="replace",
        )
        df_entities = pl.read_database_uri(
            entities_sql_query,
            uri=database_connection_uri,
        )

        if config["label"]:
            df_entities = df_entities.with_columns(
                pl.coalesce("cluster_id", "parent_id").cast(pl.String)
            )

        dfs.append(df_entities)

    with psycopg.connect(database_connection_uri) as conn, conn.cursor() as cur:
        cur.execute("DROP TABLE luis._suggestions_tmp")
        conn.commit()

    df_concat = pl.concat(dfs).select("identifiant_unique", "cluster_id")

    return df_concat.unique("identifiant_unique")


def balance_entities_dataset(
    df_entities_ml_manual_labeling: pl.DataFrame,
    df_entities_suggestions_manual_labeling: pl.DataFrame,
    df_entities_ml_inference_manual_labeling: pl.DataFrame,
    database_connection_uri: str,
    num_examples_for_each_label: int = 1000,
) -> pl.DataFrame:

    df_entities_manual_labeling = pl.concat(
        [
            df_entities_ml_manual_labeling,
            df_entities_suggestions_manual_labeling,
            df_entities_ml_inference_manual_labeling,
        ]
    ).with_columns(pl.lit("manual").alias("example_type"))

    df_entities_cluster = get_clusters_from_database_random_sampling(
        database_connection_uri, df_entities_manual_labeling
    ).with_columns(pl.lit("auto").alias("example_type"))

    cluster_ids_in_manual_dataset = (
        df_entities_manual_labeling.filter(pl.col("cluster_id").is_not_null())
        .select(pl.col("cluster_id").unique())["cluster_id"]
        .to_list()
    )
    entity_ids_in_manual_dataset = df_entities_manual_labeling.select(
        pl.col("identifiant_unique").unique()
    )["identifiant_unique"].to_list()

    # Add clusters sibling if not already in dataset
    df_final = pl.concat(
        [
            df_entities_manual_labeling,
            df_entities_cluster.filter(
                pl.col("cluster_id").is_in(cluster_ids_in_manual_dataset)
                & pl.col("identifiant_unique")
                .is_in(entity_ids_in_manual_dataset)
                .not_()
                & pl.col("was_singleton").not_()
            ).select("identifiant_unique", "cluster_id", "example_type"),
        ]
    )
    # Add clusters sibling from manual singletons that in fact are in a cluster
    df_final = pl.concat(
        [
            df_final.filter(
                pl.col("identifiant_unique")
                .is_in(
                    df_entities_cluster.filter(pl.col("was_singleton"))[
                        "identifiant_unique"
                    ]
                )
                .not_()
            ),
            df_entities_cluster.filter(
                pl.col("was_singleton")
                & pl.col("identifiant_unique")
                .is_in(entity_ids_in_manual_dataset)
                .not_()
            ).select("identifiant_unique", "cluster_id", "example_type"),
        ]
    )

    # Add required additional cluster entities
    df_entities_cluster = df_entities_cluster.filter(
        pl.col("cluster_id")
        .is_in(
            df_final.filter(pl.col("cluster_id").is_not_null())["cluster_id"].to_list()
        )
        .not_()  # Filter out entities that are already in the dataset
    )
    num_entities_with_clusters = len(
        df_final.filter(pl.col("cluster_id").is_not_null())
    )
    required_clustered_entities = (
        num_examples_for_each_label - num_entities_with_clusters
    )

    if required_clustered_entities > 0:
        logger.info(
            "Will add %s required clustered entities to reach num_examples_for_each_label",
            required_clustered_entities,
        )
        i = 0
        cluster_ids = df_entities_cluster.select(
            pl.col("cluster_id").unique().shuffle(RANDOM_SEED)
        )["cluster_id"].to_list()
        clusters_to_add = []
        while required_clustered_entities > 0:
            cluster_to_add = cluster_ids[i]
            clusters_to_add.append(cluster_to_add)
            required_clustered_entities -= len(
                df_entities_cluster.filter(pl.col("cluster_id") == cluster_to_add)
            )
            i += 1

        df_final = pl.concat(
            [
                df_final,
                df_entities_cluster.filter(
                    pl.col("cluster_id").is_in(clusters_to_add)
                ).select("identifiant_unique", "cluster_id", "example_type"),
            ]
        )

    num_entities_without_clusters = len(df_final.filter(pl.col("cluster_id").is_null()))
    required_singleton_entities = (
        num_examples_for_each_label - num_entities_without_clusters
    )
    if required_singleton_entities > 0:
        logger.info(
            "Will add %s required singleton entities to reach num_examples_for_each_label",
            required_singleton_entities,
        )
        df_singletons = get_singleton_entities_from_database_random_sampling(
            database_connection_uri, df_final
        ).with_columns(pl.lit("auto").alias("example_type"))

        df_hard_singletons = df_singletons.filter(
            pl.col("is_100m_close_to_clustered_entity")
        )
        hard_singletons_to_take = min(
            math.floor(0.25 * required_singleton_entities), len(df_hard_singletons)
        )
        df_hard_singletons_sampled = df_hard_singletons.sample(
            n=hard_singletons_to_take
        )
        df_final = pl.concat(
            [
                df_final,
                df_hard_singletons_sampled,
                df_singletons.filter(
                    pl.col("is_100m_close_to_clustered_entity").not_()
                ).sample(required_singleton_entities - hard_singletons_to_take),
            ],
            how="diagonal",
        )

    return df_final


def get_clusters_from_database_random_sampling(
    database_connection_uri: str, df_entities: pl.DataFrame
) -> pl.DataFrame:
    sql_query_folder = get_sql_files_folder_path()

    tmp_table_name = "luis._entities_tmp"
    df_entities.write_database(
        tmp_table_name,
        connection=database_connection_uri,
        if_table_exists="replace",
    )

    df_entities_cluster = pl.read_database_uri(
        query=(sql_query_folder / "cluster_entities.sql")
        .read_text()
        .format(tmp_table_name, tmp_table_name),
        uri=database_connection_uri,
    )

    with psycopg.connect(database_connection_uri) as conn, conn.cursor() as cur:
        cur.execute(f"DROP TABLE {tmp_table_name}")
        conn.commit()

    return df_entities_cluster


def get_singleton_entities_from_database_random_sampling(
    database_connection_uri: str, df_entities: pl.DataFrame
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

    tmp_table_name = "luis._entities_tmp"
    df_entities.write_database(
        tmp_table_name,
        connection=database_connection_uri,
        if_table_exists="replace",
    )

    with psycopg.connect(database_connection_uri) as conn, conn.cursor() as cur:
        cur.execute(
            (sql_query_folder / "create_singleton_entities_tmp_tables.sql")
            .read_text()
            .format(tmp_table_name, tmp_table_name)
        )
        conn.commit()

    df_entities = pl.read_database_uri(
        query=(sql_query_folder / "singleton_entities.sql")
        .read_text()
        .format(tmp_table_name),
        uri=database_connection_uri,
    )

    with psycopg.connect(database_connection_uri) as conn, conn.cursor() as cur:
        cur.execute(
            (sql_query_folder / "drop_singleton_entities_tmp_tables.sql").read_text()
        )
        cur.execute(f"DROP TABLE {tmp_table_name}")
        conn.commit()

    return df_entities
