import logging
import math
from pathlib import Path

import polars as pl
import polars_distance as pld
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
                .agg(pl.col("identifiant_unique").alias("ids"))
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
    nearby_distance_meters: float = 50,
    nearby_clusters_ratio: float = 0.5,
    name_similarity_threshold: float = 0.9,
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

    # Add clusters sibling from manual singletons that in fact are in a cluster
    singletons_with_clusters_in_db = (
        df_entities_cluster.filter(pl.col("was_singleton"))
        .get_column("identifiant_unique")
        .to_list()
    )
    df_final = pl.concat(
        [
            df_entities_manual_labeling.filter(
                pl.col("identifiant_unique")
                .is_in(singletons_with_clusters_in_db)
                .not_()
            ),
            df_entities_cluster.filter(pl.col("was_singleton")).select(
                "identifiant_unique", "cluster_id", "example_type"
            ),
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

    # =====================================================================
    # Entités de clusters DIFFERENTS mais géographiquement proches (centres
    # commerciaux). Elles ont toutes un parent_id (cluster connu) : on est
    # certain qu'elles sont distinctes -> aucun risque de faux négatif.
    # Au moment du block_df (cross-join), deux entités de clusters voisins
    # formeront une paire avec cluster_id_l != cluster_id_r -> labellisée
    # négative. C'est la source fiable de "hard negatives" proches.
    #
    # Le nombre d'entités ajoutées est borné : il représente environ
    # nearby_clusters_ratio (50 % par défaut) du budget restant pour atteindre
    # num_examples_for_each_label, le reste étant complété par les singletons.
    # =====================================================================
    num_entities_to_add = num_examples_for_each_label - len(
        df_final.filter(pl.col("cluster_id").is_null())
    )
    nearby_budget = math.floor(nearby_clusters_ratio * num_entities_to_add)
    singleton_budget = num_entities_to_add - nearby_budget

    df_nearby_clusters = get_nearby_clusters_from_database_random_sampling(
        database_connection_uri, nearby_distance_meters
    ).filter(
        pl.col("identifiant_unique")
        .is_in(df_final.get_column("identifiant_unique"))
        .not_()
    )
    if nearby_budget > 0 and not df_nearby_clusters.is_empty():
        # On ajoute des CLUSTERS ENTIERS (et non des entités isolées) : sinon,
        # un cluster partiellement ajouté se retrouverait avec une seule entité
        # dans le dataset final et son cluster_id serait remis à null par la règle
        # finale, ce qui casserait la garantie "clusters distincts connus" et
        # produirait des entités sans cluster_id malgré un parent_id en base.
        # On ne garde que les clusters ayant au moins 2 entités (vrais clusters,
        # non remis à null) et on sélectionne des clusters au hasard jusqu'à
        # approcher le budget.
        cluster_sizes = df_nearby_clusters.group_by("cluster_id").agg(
            pl.len().alias("n_entities")
        )
        cluster_sizes = cluster_sizes.filter(pl.col("n_entities") >= 2)
        shuffled_cluster_ids = cluster_sizes.select(
            pl.col("cluster_id").shuffle(RANDOM_SEED)
        )["cluster_id"].to_list()

        selected_cluster_ids = []
        budget_left = nearby_budget
        for cluster_id in shuffled_cluster_ids:
            selected_cluster_ids.append(cluster_id)
            budget_left -= cluster_sizes.filter(pl.col("cluster_id") == cluster_id)[
                "n_entities"
            ][0]
            if budget_left <= 0:
                break

        df_nearby_clusters_sampled = df_nearby_clusters.filter(
            pl.col("cluster_id").is_in(selected_cluster_ids)
        ).with_columns(pl.lit("auto_nearby").alias("example_type"))
        df_final = pl.concat([df_final, df_nearby_clusters_sampled], how="diagonal")
        logger.info(
            "Added %s nearby-cluster entities across %s clusters "
            "(shopping malls hard negatives)",
            len(df_nearby_clusters_sampled),
            len(selected_cluster_ids),
        )

    if singleton_budget > 0:
        logger.info(
            "Will add %s required singleton entities to reach num_examples_for_each_label",
            singleton_budget,
        )
        df_singletons = get_singleton_entities_from_database_random_sampling(
            database_connection_uri, df_final
        ).with_columns(pl.lit("auto_singleton").alias("example_type"))

        # =================================================================
        # Filtre anti-faux-négatif : un singleton proche d'une entité déjà
        # présente dans le dataset avec un nom quasi identique est très
        # probablement un doublon non détecté. On ne doit PAS l'ajouter comme
        # négatif, sinon on injecte du bruit. On garde uniquement les
        # singletons proches dont le nom diffère nettement, plus les
        # singletons isolés (> seuil de proximité).
        # =================================================================
        df_singletons = filter_singletons_not_duplicates(
            df_singletons, name_similarity_threshold
        )

        df_hard_singletons = df_singletons.filter(
            pl.col("is_100m_close_to_clustered_entity")
        )
        hard_singletons_to_take = min(
            math.floor(0.25 * singleton_budget), len(df_hard_singletons)
        )
        df_hard_singletons_sampled = df_hard_singletons.sample(
            n=hard_singletons_to_take
        )
        df_isolated_singletons = df_singletons.filter(
            pl.col("is_100m_close_to_clustered_entity").not_()
        )
        isolated_to_take = min(
            singleton_budget - hard_singletons_to_take, len(df_isolated_singletons)
        )
        df_isolated_singletons_sampled = df_isolated_singletons.sample(
            n=isolated_to_take
        )
        df_final = pl.concat(
            [
                df_final,
                df_hard_singletons_sampled,
                df_isolated_singletons_sampled,
            ],
            how="diagonal",
        )

    # Some entities are in clusters with only one entities due for example to deletions of siblings
    # We set their cluster_id to null

    df_final = df_final.with_columns(
        pl.when(pl.col("identifiant_unique").count().over("cluster_id") == 1)
        .then(None)
        .otherwise("cluster_id")
        .alias("cluster_id")
    )

    return df_final


def filter_singletons_not_duplicates(
    df_singletons: pl.DataFrame,
    name_similarity_threshold: float = 0.9,
) -> pl.DataFrame:
    """Remove singletons that are likely duplicate records of entities already
    present in the dataset (false negatives).

    A singleton close to an existing dataset entity (is_100m_close_to_clustered_entity)
    whose name is very similar to one of the nearby entities is very likely a
    non-detected duplicate. We exclude it from the negative pool to avoid adding
    noise, keeping only the singletons whose name differs clearly plus the
    isolated ones.

    Parameters
    ----------
    df_singletons : pl.DataFrame
        Singleton entities as returned by singleton_entities.sql, with the extra
        columns `nom` and `close_entities_noms`.
    name_similarity_threshold : float, optional
        Jaro-Winkler similarity above which two names are considered identical.
        Default is 0.9.

    Returns
    -------
    pl.DataFrame
        The singletons filtered of likely duplicates.
    """
    if df_singletons.is_empty() or "close_entities_noms" not in df_singletons.columns:
        return df_singletons

    df_singletons = df_singletons.with_columns(
        pl.col("close_entities_noms").fill_null(pl.lit([])).alias("close_entities_noms")
    )

    df_proximity = (
        df_singletons.select("identifiant_unique", "nom", "close_entities_noms")
        .explode("close_entities_noms")
        .filter(pl.col("close_entities_noms").is_not_null())
        .with_columns(
            pld.col("nom")
            .dist_str.jaro_winkler("close_entities_noms")
            .alias("name_sim")
        )
        .group_by("identifiant_unique")
        .agg(pl.col("name_sim").max().alias("max_name_sim"))
    )

    df_singletons = df_singletons.join(
        df_proximity, on="identifiant_unique", how="left"
    ).with_columns(pl.col("max_name_sim").fill_null(0.0).alias("max_name_sim"))

    # Un singleton proche d'une entité existante dont le nom est trop similaire
    # est exclu (probable doublon -> faux négatif).
    df_singletons = df_singletons.filter(
        ~(
            pl.col("is_100m_close_to_clustered_entity")
            & (pl.col("max_name_sim") >= name_similarity_threshold)
        )
    ).drop(["nom", "close_entities_noms", "max_name_sim"])

    return df_singletons


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
        .format(tmp_table_name, tmp_table_name, tmp_table_name),
        uri=database_connection_uri,
    )

    with psycopg.connect(database_connection_uri) as conn, conn.cursor() as cur:
        cur.execute(f"DROP TABLE {tmp_table_name}")
        conn.commit()

    return df_entities_cluster


def get_nearby_clusters_from_database_random_sampling(
    database_connection_uri: str,
    nearby_distance_meters: float = 50,
    sample_size: int = 5000,
) -> pl.DataFrame:
    """Retrieve entities from distinct clusters (parent_id) that are geographically
    close (<= nearby_distance_meters). This is the typical case of shopping malls
    where several distinct shops are located at the same place.

    These entities all have a parent_id (known cluster), so we are certain they
    are distinct entities -> no risk of adding noise / false negatives.

    The candidates are materialized in a temporary table with a GiST index on
    "location" (guaranteeing the spatial index is used, unlike querying the view
    directly), and the spatial self-join is bounded: only a random sample of
    `sample_size` acteurs drives the neighborhood lookup, each of them only
    searching its close neighbors via the GiST index. This keeps the query fast
    even on a large table instead of doing a full cross spatial join.

    Parameters
    ----------
    database_connection_uri : str
        URI for the database connection.
    nearby_distance_meters : float, optional
        Maximum distance (meters) below which two entities of distinct clusters
        are considered nearby. Default is 50.
    sample_size : int, optional
        Number of randomly sampled acteurs that drive the nearby lookup.
        Default is 5000.

    Returns
    -------
    pl.DataFrame
        DataFrame with columns:
        - identifiant_unique: The entity's unique identifier.
        - cluster_id: The entity's parent_id cast to String.
    """
    sql_query_folder = get_sql_files_folder_path()

    with psycopg.connect(database_connection_uri) as conn, conn.cursor() as cur:
        cur.execute(
            (sql_query_folder / "create_nearby_clusters_tmp_tables.sql").read_text()
        )
        conn.commit()

    df_entities_nearby_clusters = pl.read_database_uri(
        query=(sql_query_folder / "nearby_clusters.sql")
        .read_text()
        .format(nearby_distance_meters=nearby_distance_meters, sample_size=sample_size),
        uri=database_connection_uri,
    ).with_columns(pl.col("cluster_id").cast(pl.String))

    with psycopg.connect(database_connection_uri) as conn, conn.cursor() as cur:
        cur.execute(
            (sql_query_folder / "drop_nearby_clusters_tmp_tables.sql").read_text()
        )
        conn.commit()

    return df_entities_nearby_clusters


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
