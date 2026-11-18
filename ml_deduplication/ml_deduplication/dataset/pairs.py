from pathlib import Path

import polars as pl
import psycopg

from ml_deduplication.dataset import RANDOM_SEED
from ml_deduplication.dataset.utils import get_sql_files_folder_path


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


def create_entity_pairs_from_ml_inference_manual_labeling(
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
        - identifiant_unique_i: The first actor's unique identifier.
        - identifiant_unique_j: The second actor's unique identifier.
        - label: Boolean indicating if the pair is a match.
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
                df.group_by("cluster_label")
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

            df_pairs = (
                (
                    df.join(df, on="cluster_label", suffix="_j")
                    .filter(
                        pl.col("identifiant_unique") != pl.col("identifiant_unique_j")
                    )
                    .with_columns(
                        pl.min_horizontal(
                            ["identifiant_unique", "identifiant_unique_j"]
                        ).alias("identifiant_unique_i"),
                        pl.max_horizontal(
                            ["identifiant_unique", "identifiant_unique_j"]
                        ).alias("identifiant_unique_j"),
                    )
                    .unique(["identifiant_unique_i", "identifiant_unique_j"])
                    .with_columns(
                        pl.when(
                            (pl.col("Review") == "OK") & (pl.col("Review_j") == "OK")
                        )
                        .then(True)
                        .when(
                            (pl.col("Review") == "Pas ok")
                            & (pl.col("Review_j") == "Pas ok")
                        )
                        .then(False)
                        .when(
                            (
                                (pl.col("Review") == "OK")
                                & (pl.col("Review_j") == "Pas ok")
                            )
                            | (
                                (pl.col("Review") == "Pas ok")
                                & (pl.col("Review_j") == "OK")
                            )
                        )
                        .then(False)
                        .when(
                            (
                                (pl.col("Review") == "Partiellement ok")
                                & (pl.col("Review_j") == "Pas ok")
                            )
                            | (
                                (pl.col("Review") == "Pas ok")
                                & (pl.col("Review_j") == "Partiellement ok")
                            )
                        )
                        .then(False)
                        .when(
                            (pl.col("Review") == "Partiellement ok")
                            & (pl.col("Review_j") == "Partiellement ok")
                        )
                        .then(True)
                        .otherwise(None)
                        .alias("label"),
                    )
                )
                .join(df_cluster_ids, on="cluster_label")
                .select(
                    [
                        "identifiant_unique_i",
                        "identifiant_unique_j",
                        "cluster_id",
                        "label",
                    ]
                )
                .with_columns(
                    pl.when(pl.col("label")).then("cluster_id").otherwise(None)
                )
            )

            dfs_to_concat.append(df_pairs)

        elif cluster_colname == "cluster_id":  # New annotation style
            df = df.select(
                ["identifiant_unique", cluster_colname, "review", "cluster_id_manual"]
            )
            df = df.filter(pl.col("review").is_not_null())

            df_pairs = (
                (
                    df.join(df, on=cluster_colname, suffix="_j")
                    .filter(
                        pl.col("identifiant_unique") != pl.col("identifiant_unique_j")
                    )
                    .with_columns(
                        pl.min_horizontal(
                            ["identifiant_unique", "identifiant_unique_j"]
                        ).alias("identifiant_unique_i"),
                        pl.max_horizontal(
                            ["identifiant_unique", "identifiant_unique_j"]
                        ).alias("identifiant_unique_j"),
                    )
                    .unique(["identifiant_unique_i", "identifiant_unique_j"])
                    .with_columns(
                        pl.when(
                            (pl.col("review") == "OK") & (pl.col("review_j") == "OK")
                        )
                        .then(True)
                        .when(
                            (pl.col("review") == "Pas ok")
                            & (pl.col("review_j") == "Pas ok")
                        )
                        .then(False)
                        .when(
                            (
                                (pl.col("review") == "OK")
                                & (pl.col("review_j") == "Pas ok")
                            )
                            | (
                                (pl.col("review") == "Pas ok")
                                & (pl.col("review_j") == "OK")
                            )
                        )
                        .then(False)
                        .when(
                            (
                                (pl.col("review") == "Partiellement ok")
                                & (pl.col("review_j") == "Pas ok")
                            )
                            | (
                                (pl.col("review") == "Pas ok")
                                & (pl.col("review_j") == "Partiellement ok")
                            )
                        )
                        .then(False)
                        .when(
                            (
                                (pl.col("review") == "Partiellement ok")
                                & (pl.col("review_j") == "Partiellement ok")
                            )
                            & (
                                (
                                    pl.col("cluster_id_manual")
                                    == pl.col("cluster_id_manual_j")
                                )
                                | (
                                    pl.col("cluster_id_manual").is_null()
                                    & pl.col("cluster_id_manual_j").is_null()
                                )
                            )
                        )
                        .then(True)
                        .when(
                            (
                                (pl.col("review") == "Partiellement ok")
                                & (pl.col("review_j") == "Partiellement ok")
                            )
                            & (
                                pl.col("cluster_id_manual")
                                != pl.col("cluster_id_manual_j")
                            )
                        )
                        .then(False)
                        .otherwise(None)
                        .alias("label"),
                    )
                    .with_columns(
                        pl.when(
                            (
                                (pl.col("review") == "Partiellement ok")
                                & (pl.col("review_j") == "Partiellement ok")
                            )
                            & (
                                pl.col("cluster_id_manual")
                                == pl.col("cluster_id_manual_j")
                            )
                        )
                        .then("cluster_id_manual")
                        .otherwise("cluster_id")
                        .alias("cluster_id")
                    )
                )
                .select(
                    [
                        "identifiant_unique_i",
                        "identifiant_unique_j",
                        "cluster_id",
                        "label",
                    ]
                )
                .with_columns(
                    pl.when(pl.col("label")).then("cluster_id").otherwise(None)
                )
            )

            dfs_to_concat.append(df_pairs)

    final_df = pl.concat(dfs_to_concat)
    return final_df.unique(["identifiant_unique_i", "identifiant_unique_j"])


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

        if "true_candidate_filter" not in df_suggestions.columns:
            df_suggestions = df_suggestions.with_columns(
                pl.lit(None).alias("true_candidate_filter")
            )
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

    with psycopg.connect(database_connection_uri) as conn, conn.cursor() as cur:
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
