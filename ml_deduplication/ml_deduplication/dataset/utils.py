from pathlib import Path

import polars as pl


def get_sql_files_folder_path() -> Path:
    sql_query_folder = Path(__file__).parent / "sql"

    return sql_query_folder


def balance_pairs_dataset(
    df_pairs_ml_manual_labeling: pl.DataFrame | None,
    df_pairs_manual_labeling: pl.DataFrame | None,
    df_pairs_ml_inference_manual_labeling: pl.DataFrame | None,
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
    df_pairs_ml_inference_manual_labeling : pl.DataFrame
        Pairs from ML inference manual labeling.
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
            e.with_columns(pl.lit("manual").alias("example_type"))
            for e in [
                df_pairs_ml_manual_labeling,
                df_pairs_ml_inference_manual_labeling,
                df_pairs_manual_labeling,
            ]
            if e is not None
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
            df_pairs_database_random_sampling.filter(
                pl.col("label")
                & (
                    pl.col("identifiant_unique_i")
                    .is_in(df_pairs.get_column("identifiant_unique_i"))
                    .not_()
                )
                & (
                    pl.col("identifiant_unique_j")
                    .is_in(df_pairs.get_column("identifiant_unique_j"))
                    .not_()
                )
            )
            .filter(
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
            )
            .with_columns(pl.lit("auto").alias("example_type")),
        ],
        how="diagonal",
    )

    positive_ids = set(
        df_pairs.filter(pl.col("label"))
        .select(
            pl.concat_list(
                ["identifiant_unique_i", "identifiant_unique_j"]
            ).list.explode()
        )
        .unique()
        .get_column("identifiant_unique_i")
        .to_list()
    )

    # Hard negatives: at least one ID appears in positive pairs
    hard_negatives = df_pairs_database_random_sampling.filter(
        pl.col("label").not_()
        & (
            pl.col("identifiant_unique_i").is_in(positive_ids)
            | pl.col("identifiant_unique_j").is_in(positive_ids)
        )
    )

    # Fallback to easy negatives if hard negatives pool is too small
    negatives_needed = num_examples_for_each_label - len(
        df_pairs.filter(pl.col("label").not_())
    )

    hard_negatives_sampled = hard_negatives.sample(
        n=min(negatives_needed, len(hard_negatives)), seed=42
    ).with_columns(pl.lit("auto").alias("example_type"))
    negatives_dfs = [hard_negatives_sampled]
    if len(hard_negatives) < negatives_needed:
        # Pairs already in dataset (to avoid contradictions)
        existing_pairs = (
            hard_negatives_sampled.select(
                pl.concat_arr(["identifiant_unique_i", "identifiant_unique_j"])
            )
            .get_column("identifiant_unique_i")
            .to_list()
        )
        easy_negatives = (
            df_pairs_database_random_sampling.filter(
                pl.col("label").not_()
                & (
                    pl.concat_list(["identifiant_unique_i", "identifiant_unique_j"])
                    .is_in(existing_pairs)
                    .not_()
                )
            )
            .sample(n=negatives_needed - len(hard_negatives_sampled), seed=42)
            .with_columns(pl.lit("auto").alias("example_type"))
        )
        negatives_dfs.append(easy_negatives)

    df_pairs = pl.concat([df_pairs, *negatives_dfs], how="diagonal")

    # Remove any contradictory duplicates (same pair, different labels)
    df_pairs = df_pairs.unique(
        subset=["identifiant_unique_i", "identifiant_unique_j"],
        keep="first",  # Keeps the manually labeled version if it exists
    )

    return df_pairs
