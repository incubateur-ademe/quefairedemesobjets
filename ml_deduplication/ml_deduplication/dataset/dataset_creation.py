"""Module used to create the dataset of acteur pairs that will then used in training.
The dataset is created using different methods like manual annotation and random sampling.
"""

import os
from pathlib import Path

import polars as pl

RANDOM_SEED = 42


def create_entity_pairs_from_ml_manual_labeling(
    ml_manual_labeling_datasets_folder_path: Path,
) -> pl.DataFrame:
    """Create acteurs pairs from manual labeling of the old ML experience.
    See original spreadsheet : https://docs.google.com/spreadsheets/d/1HltmT0Rhq-NXHaRJpDeqNEXXHO87iZMKTl7144iZaJ4/edit?gid=154092679#gid=154092679
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
    pairs_sql_query = (
        (Path(__file__).parent / "sql" / "pairs_query.sql")
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

    df_pairs = pl.concat(dfs)

    return df_pairs


def create_entity_pairs_from_database_parent_changes(
    database_connection_uri: str,
) -> pl.DataFrame:
    sql_query_folder = Path(__file__).parent / "sql"

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
    sql_query_folder = Path(__file__).parent / "sql"
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
    df_pairs = pl.concat(
        [
            df_pairs_ml_manual_labeling,
            df_pairs_database_via_parent_change,
            df_pairs_manual_labeling,
        ],
        how="diagonal",
    )

    df_pairs = pl.concat(
        [
            df_pairs,
            df_pairs_database_random_sampling.filter(pl.col("label").not_()).sample(
                n=(1000 - len(df_pairs.filter(pl.col("label").not_()))),
                seed=42,
            ),
            df_pairs_database_random_sampling.filter(pl.col("label")).filter(
                pl.col("cluster_id").is_in(
                    df_pairs_database_random_sampling.select(
                        pl.col("cluster_id").unique()
                    )
                    .sample(
                        n=int(
                            (1000 - len(df_pairs.filter(pl.col("label")))) / 2.1
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
    datasets_path: Path, database_connection_uri: str
) -> pl.DataFrame:
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
    )

    return df_pairs_balanced


if __name__ == "__main__":
    datasets_path = Path(os.environ["ML_DATASETS_PATH"])
    database_connection_uri = os.environ["DATABASE_CONNECTION_URI"]
    df_pairs = create_full_dataset(datasets_path, database_connection_uri)
