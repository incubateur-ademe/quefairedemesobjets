import logging
import os
import resource
import sys

import duckdb
import polars as pl

logger = logging.getLogger(__name__)

# Where duckdb spills to disk during blocking. The default CWD (/app in the
# inference image) is read-only for the non-root runtime user, so we redirect
# the temp storage to a dedicated writable directory (see the Dockerfile).
DUCKDB_TEMP_DIR = os.environ.get("DUCKDB_TEMP_DIR", "/tmp/duckdb")
# Bound duckdb's in-memory footprint so the (potentially very large) blocking
# joins and the materialized feature table spill to disk instead of competing
# with the rest of the inference process for RAM. Overridable via the env var.
DUCKDB_MEMORY_LIMIT = os.environ.get("DUCKDB_MEMORY_LIMIT", None)


def _rss_mb() -> float:
    """Return the current peak resident set size in MB.

    ``ru_maxrss`` is reported in bytes on macOS but in kilobytes on Linux, so the
    unit must be converted per-platform for the log to be meaningful.
    """
    ru_maxrss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return ru_maxrss / 1024 / 1024
    return ru_maxrss / 1024


def _prepare_pairs_final_table(
    df_features: pl.DataFrame,
    additional_business_rules_sql_exprs: list[str] | None = None,
    additional_columns_to_keep: list[str] | None = None,
) -> tuple[duckdb.DuckDBPyConnection | None, int]:
    """Run the duckdb blocking pipeline and leave candidate pairs ready to join.

    Blocks candidate pairs (siren / departement / geo predicates, deduplicated
    by hashed buckets) into the ``pairs_minimal`` table and registers the
    feature tables needed by the final pair/feature joins. Intermediate
    blocking tables are dropped to free the duckdb baseline.

    Args:
        df_features: Preprocessed entities frame (output of `preprocess_features`).
        additional_business_rules_sql_exprs: Extra SQL predicates ANDed into the
            blocking filter.
        additional_columns_to_keep: Entity columns to carry through as ``_l``/``_r``
            in the output.

    Returns:
        A tuple ``(con, n_pairs)``. If no candidate pairs were found, ``con`` is
        ``None`` (connection already closed) and ``n_pairs`` is ``0``. Otherwise
        ``con`` holds ``pairs_minimal``, ``features_full`` and ``features_vector``
        and is left open for the caller to build its final table and stream over.
    """
    os.makedirs(DUCKDB_TEMP_DIR, exist_ok=True)
    config = {"temp_directory": DUCKDB_TEMP_DIR}
    if DUCKDB_MEMORY_LIMIT is not None:
        config["memory_limit"] = DUCKDB_MEMORY_LIMIT
    con = duckdb.connect(config=config)
    con.install_extension("spatial")
    con.load_extension("spatial")

    cols_needed = [
        "identifiant_unique",
        "siren",
        "code_postal",
        "latitude",
        "longitude",
        "source_id",
        "acteur_type_id",
    ]
    if additional_columns_to_keep is not None:
        for colname in additional_columns_to_keep:
            if colname not in cols_needed:
                cols_needed.append(colname)

    business_rules_filter_sql = """
    (
        (coalesce(acteur_type_id_l,-1)=coalesce(acteur_type_id_r,-1))
        OR (
            acteur_type_id_l=4 AND acteur_type_id_r=3
        )
        OR (
            acteur_type_id_l=3 AND acteur_type_id_r=4
        )
    )
    AND (
        coalesce(source_id_l,-1) <> coalesce(source_id_r,-2)
    )
"""
    if additional_business_rules_sql_exprs is not None:
        for additional_rule in additional_business_rules_sql_exprs:
            business_rules_filter_sql += f"AND ({additional_rule})"

    business_rules_filter_sql = f"({business_rules_filter_sql})"

    # Optimize types immediately and register the minimal schema for blocking.
    df_minimal = df_features.select(cols_needed).with_columns(
        [
            pl.col("latitude").cast(pl.Float32),
            pl.col("longitude").cast(pl.Float32),
        ]
    )
    con.register("df_minimal", df_minimal)
    con.sql("""CREATE TABLE features AS
        SELECT *,
               ST_Point2D(longitude,latitude) as location
        FROM df_minimal
    """)

    # =====================================================================
    # ÉTAPE 1 : Génération de candidats sur le schéma minimal
    # =====================================================================

    # 1. SIREN
    con.sql(f"""
    CREATE table blocking_siren AS (
        with joined as (
            SELECT
                columns(l.*) as '\\0_l',
                columns(r.*) as '\\0_r',
            from
                features l
            inner join features r on
                l.siren=r.siren
        )
        SELECT
            identifiant_unique_l,
            identifiant_unique_r
        from joined
        where identifiant_unique_l < identifiant_unique_r
        AND {business_rules_filter_sql}
    )
""")

    logger.info(
        "Blocking: siren predicate -> %s candidates ",
        con.sql("SELECT count(*) FROM blocking_siren").fetchone()[0],
    )

    # 2. Code Postal
    con.sql(f"""
    CREATE table blocking_departement AS (
        with joined as (
            SELECT
                columns(l.*) as '\\0_l',
                columns(r.*) as '\\0_r',
            from
                features l
            inner join features r on
                l.code_postal[:2]=r.code_postal[:2]
        )
        SELECT
            identifiant_unique_l,
            identifiant_unique_r
        from joined
        where identifiant_unique_l < identifiant_unique_r
        AND {business_rules_filter_sql}
    )
    """)
    logger.info(
        "Blocking: cp predicate -> %s candidates ",
        con.sql("SELECT count(*) FROM blocking_departement").fetchone()[0],
    )

    # 3. Grille Géographique optimisée en jointure grace à ST_DWITHIN (distance en degré, correspond à 15km)
    con.sql("""
    CREATE table blocking_geo_temp AS (
        SELECT
            columns(l.*) as '\\0_l',
            columns(r.*) as '\\0_r',
        from
            features l
        inner join features r on
            ST_DWithin(
                l.location,
                r.location,
                0.14
            )
    )
    """)

    con.sql(f"""
    CREATE table blocking_geo AS (
        SELECT
            identifiant_unique_l,
            identifiant_unique_r
        from blocking_geo_temp
        where identifiant_unique_l < identifiant_unique_r
        AND {business_rules_filter_sql}
    )
    """)

    logger.info(
        "Blocking: geo predicate -> %s candidates",
        con.sql("SELECT count(*) FROM blocking_geo").fetchone()[0],
    )

    # =====================================================================
    # ÉTAPE 3 : Union + dédoublonnage par buckets (mémoire bornée)
    # =====================================================================
    # Les trois prédicats ont été réduits AVANT dédoublonnage (distance + règles
    # métier), donc la concaténation ne fait pas exploser la mémoire. Le
    # dédoublonnage est ensuite partitionné en `dedup_buckets` buckets via un
    # hash déterministe de la paire (l, r) : chaque `unique()` n'opère que sur
    # un bucket, donc la table de hachage est bornée par la taille du plus gros
    # bucket — pas par l'ensemble complet. C'est ce qui supprime le pic ~200GB.
    logger.info("Collecting minimal valid pairs to free memory...")
    con.sql("""
        CREATE table pairs AS (
        with all_data as (
        SELECT
            identifiant_unique_l,
            identifiant_unique_r
        from blocking_siren
        UNION ALL
        SELECT
            identifiant_unique_l,
            identifiant_unique_r
        from blocking_departement
        UNION ALL
        SELECT
            identifiant_unique_l,
            identifiant_unique_r
        from blocking_geo
        )
        SELECT
            identifiant_unique_l,
            identifiant_unique_r
        from all_data
        group by 1,2)
            """)

    logger.info(
        "Blocking: dedup complete -> %s valid candidate pairs ",
        con.sql("SELECT count(*) FROM pairs").fetchone()[0],
    )
    con.sql("CHECKPOINT;")
    con.sql("""
    CREATE TABLE pairs_minimal AS (
        SELECT
            identifiant_unique_l,
            identifiant_unique_r,
            ST_DISTANCE_Spheroid(
                ST_Point2D(f.latitude,f.longitude),
                ST_Point2D(f2.latitude,f2.longitude)
            ) as geo_distance
        FROM pairs p
        left join features f on p.identifiant_unique_l=f.identifiant_unique
        left join features f2 on p.identifiant_unique_r=f2.identifiant_unique
    )
    """)

    n_pairs = con.sql("SELECT count(*) FROM pairs_minimal").fetchone()[0]
    if n_pairs == 0:
        # Aucune paire trouvée : on ferme et on signale le cas vide.
        con.close()
        return None, 0

    # On prépare les tables de features pour les jointures finales. On n'emporte
    # QUE les features scalaires dans la jointure : la colonne
    # adresse_clean_vector (1024 x Float32) est exclue et exposée dans une table
    # dédiée `features_vector`, jointe uniquement pour le calcul du cosine.
    column_needed_to_generate_features = [
        "identifiant_unique",
        "nom_clean",
        "ville_clean",
        "siren",
        "siret",
        "telephone",
        "code_commune_insee",
        "code_postal",
        "acteur_type_id",
    ]
    if additional_columns_to_keep is not None:
        column_needed_to_generate_features.extend(additional_columns_to_keep)
        column_needed_to_generate_features = list(
            set(column_needed_to_generate_features)
        )

    con.register(
        "features_full",
        df_features.select(column_needed_to_generate_features),
    )

    # Libère la baseline duckdb : on garde uniquement `pairs_minimal`
    # (l, r, geo_distance) et la table `features_full`, on supprime les tables
    # candidates intermédiaires du blocking pour réduire l'empreinte mémoire.
    for table in [
        "blocking_siren",
        "blocking_departement",
        "blocking_geo",
        "blocking_geo_temp",
        "features",
    ]:
        con.sql(f"DROP TABLE IF EXISTS {table}")
    con.sql("CHECKPOINT;")
    logger.info("Finished blocking (RSS %.0f MB).", _rss_mb())
    return con, n_pairs


def _build_pairs_features_table(
    con: duckdb.DuckDBPyConnection,
    df_features: pl.DataFrame,
    additional_columns_to_keep: list[str] | None = None,
) -> None:
    """Materialize the slim `pairs_features` table with all features in duckdb.

    Computes every model feature in SQL in a single pass over ``pairs_minimal``,
    producing a slim table of scalar columns. Only this slim table is exported
    to polars downstream — never the fat pair join nor the 1024-dim vectors.
    ``pairs_minimal``, ``features_full`` and the freshly-registered
    ``features_vector`` are dropped once the slim table exists, and it is sorted
    once so it can be streamed by a cheap sequential scan.

    Args:
        con: Open duckdb connection with ``pairs_minimal`` and ``features_full``
            registered (output of `_prepare_pairs_final_table`).
        df_features: Preprocessed entities frame, used to register the address
            vectors needed by the cosine distance.
        additional_columns_to_keep: Entity columns to carry through as
            ``_l``/``_r`` (skips ``acteur_type_id`` already emitted as a feature).

    Note:
        ``jaro_winkler_similarity`` / ``list_cosine_similarity`` return a
        SIMILARITY (1 = identical) whereas the polars pipeline produces a
        DISTANCE (0 = identical); the ``1 - ...`` complement keeps values
        byte-identical.
    """
    con.register(
        "features_vector",
        df_features.select("identifiant_unique", "adresse_clean_vector"),
    )

    feature_exprs = [
        (
            "nom_clean_dist",
            "1 - jaro_winkler_similarity(f.nom_clean, f2.nom_clean)",
        ),
        (
            "ville_clean_dist",
            "1 - jaro_winkler_similarity(f.ville_clean, f2.ville_clean)",
        ),
        (
            "adresse_clean_distance",
            (
                "coalesce(CASE "
                "WHEN v_l.adresse_clean_vector IS NULL OR v_r.adresse_clean_vector IS NULL "
                "THEN NULL "
                "ELSE 1 - list_cosine_similarity("
                "v_l.adresse_clean_vector, v_r.adresse_clean_vector) "
                "END, 'NaN'::REAL)"
            ),
        ),
        ("siren_match", "f.siren = f2.siren"),
        ("siret_match", "f.siret = f2.siret"),
        ("telephone_match", "f.telephone = f2.telephone"),
        ("code_commune_insee_match", "f.code_commune_insee = f2.code_commune_insee"),
        ("code_postal_match", "f.code_postal = f2.code_postal"),
        (
            "departement_match",
            "substr(f.code_postal, 1, 2) = substr(f2.code_postal, 1, 2)",
        ),
        ("acteur_type_id_l", "f.acteur_type_id"),
        ("acteur_type_id_r", "f2.acteur_type_id"),
    ]

    # Colonnes `_l/_r` supplémentaires demandées (source_id, parent_id, colonnes
    # de linkage…). acteur_type_id est déjà une feature, on l'exclut.
    feature_l_names = {name for name, _ in feature_exprs}
    additional_pair_exprs = []
    if additional_columns_to_keep is not None:
        for col in additional_columns_to_keep:
            if f"{col}_l" not in feature_l_names:
                additional_pair_exprs.append(f"f.{col} AS {col}_l")
                additional_pair_exprs.append(f"f2.{col} AS {col}_r")

    # Column order must mirror the polars `generate_features` output so the two
    # paths are interchangeable (batch concatenation equals the full pipeline).
    ordered_features = [
        "nom_clean_dist",
        "adresse_clean_distance",
        "ville_clean_dist",
        "siren_match",
        "siret_match",
        "telephone_match",
        "code_commune_insee_match",
        "code_postal_match",
        "departement_match",
        "geo_distance",
        "acteur_type_id_l",
        "acteur_type_id_r",
    ]
    expr_by_name = {name: expr for name, expr in feature_exprs}
    ordered_select = []
    for name in ordered_features:
        if name == "geo_distance":
            ordered_select.append("    p.geo_distance,")
        else:
            ordered_select.append(f"    {expr_by_name[name]} AS {name},")
    select_lines = "\n".join(
        [
            "    p.identifiant_unique_l,",
            "    p.identifiant_unique_r,",
            *ordered_select,
            *[f"    {expr}," for expr in additional_pair_exprs],
        ]
    ).rstrip(",")

    con.sql(f"""
        CREATE TABLE pairs_features AS
        (
            SELECT
{select_lines}
            FROM pairs_minimal p
            left join features_full f on p.identifiant_unique_l=f.identifiant_unique
            left join features_full f2 on p.identifiant_unique_r=f2.identifiant_unique
            left join features_vector v_l on p.identifiant_unique_l=v_l.identifiant_unique
            left join features_vector v_r on p.identifiant_unique_r=v_r.identifiant_unique
        )
        """)

    for table in ["pairs_minimal"]:
        con.sql(f"DROP TABLE IF EXISTS {table}")
    for view in ["features_full", "features_vector"]:
        con.sql(f"DROP VIEW IF EXISTS {view}")
    con.sql("CHECKPOINT;")

    # Trie une seule fois en amont : le streaming par `to_arrow_reader` est alors
    # un scan séquentiel ordonné, sans re-tri ni OFFSET par lot.
    con.sql("""
        CREATE TABLE pairs_features_sorted AS
        SELECT * FROM pairs_features
        ORDER BY identifiant_unique_l, identifiant_unique_r
    """)
    con.sql("DROP TABLE pairs_features")
    con.sql("ALTER TABLE pairs_features_sorted RENAME TO pairs_features")
    con.sql("CHECKPOINT;")


def block_features_batches(
    df_features: pl.DataFrame,
    additional_business_rules_sql_exprs: list[str] | None = None,
    additional_columns_to_keep: list[str] | None = None,
    batch_size: int = 1_000_000,
):
    """Stream slim feature batches computed in duckdb.

    Streaming counterpart of :func:`block_df` for the batched inference path.
    It runs the duckdb blocking step, computes every feature in SQL into a slim
    ``pairs_features`` table, then streams it in ordered Arrow record batches of
    ``batch_size`` rows, converted on the fly to polars.

    A single sequential scan is used (no ``LIMIT/OFFSET`` re-scan) and each
    yielded frame only carries slim scalar features, so resident memory stays
    flat across batches.

    Args:
        df_features: Preprocessed entities frame.
        additional_business_rules_sql_exprs: Extra SQL predicates for blocking.
        additional_columns_to_keep: Entity columns carried as ``_l``/``_r``.
        batch_size: Number of rows per yielded batch.

    Yields:
        Polars DataFrames of slim candidate-pair features.
    """
    con, n_pairs = _prepare_pairs_final_table(
        df_features,
        additional_business_rules_sql_exprs,
        additional_columns_to_keep,
    )
    if con is None or n_pairs == 0:
        return

    try:
        _build_pairs_features_table(con, df_features, additional_columns_to_keep)
        reader = con.execute(
            "SELECT * FROM pairs_features "
            "ORDER BY identifiant_unique_l, identifiant_unique_r"
        ).to_arrow_reader(batch_size=batch_size)
        for batch_arrow in reader:
            yield pl.from_arrow(batch_arrow)
            logger.info("Streamed feature batch (RSS %.0f MB)", _rss_mb())
    finally:
        con.close()


def block_df_batches(
    df_features: pl.DataFrame,
    additional_business_rules_sql_exprs: list[str] | None = None,
    additional_columns_to_keep: list[str] | None = None,
    batch_size: int = 1_000_000,
):
    """Yield batches of raw candidate pairs from the duckdb blocking step.

    Generator version of :func:`block_df`: instead of materializing the full
    pairs frame in memory, it streams the already-computed ``pairs_final``
    duckdb table in ordered batches of ``batch_size`` rows. Each batch is a
    polars :class:`DataFrame`. The duckdb connection stays open for the whole
    iteration and is closed when the generator is exhausted (or garbage
    collected).

    Args:
        df_features: Preprocessed entities frame.
        additional_business_rules_sql_exprs: Extra SQL predicates for blocking.
        additional_columns_to_keep: Entity columns carried as ``_l``/``_r``.
        batch_size: Number of rows per yielded batch.

    Yields:
        Polars DataFrames of raw candidate pairs.
    """
    con, n_pairs = _prepare_pairs_final_table(
        df_features,
        additional_business_rules_sql_exprs,
        additional_columns_to_keep,
    )
    if con is None or n_pairs == 0:
        return

    try:
        con.sql("""
            CREATE TABLE pairs_final AS
            (
                SELECT
                    p.identifiant_unique_l,
                    p.identifiant_unique_r,
                    p.geo_distance,
                    columns(f.* EXCLUDE identifiant_unique) as '\\0_l',
                    columns(f2.* EXCLUDE identifiant_unique) as '\\0_r'
                FROM pairs_minimal p
                left join features_full f on p.identifiant_unique_l=f.identifiant_unique
                left join features_full f2 on p.identifiant_unique_r=f2.identifiant_unique
            )
        """)
        con.sql("CHECKPOINT;")
        reader = con.execute(
            "SELECT * FROM pairs_final "
            "ORDER BY identifiant_unique_l, identifiant_unique_r"
        ).to_arrow_reader(batch_size=batch_size)
        for batch_arrow in reader:
            yield pl.from_arrow(batch_arrow)
    finally:
        con.close()


def block_df(
    df_features: pl.DataFrame,
    additional_business_rules_sql_exprs: list[str] | None = None,
    additional_columns_to_keep: list[str] | None = None,
) -> pl.DataFrame:
    batches = list(
        block_df_batches(
            df_features,
            additional_business_rules_sql_exprs,
            additional_columns_to_keep,
        )
    )
    if not batches:
        # Retourner un dataframe vide avec le schéma attendu si aucune paire n'est trouvée
        return pl.DataFrame(
            schema={
                "identifiant_unique_l": pl.String,
                "identifiant_unique_r": pl.String,
                "geo_distance": pl.Float64,
            }
        )
    return pl.concat(batches)
