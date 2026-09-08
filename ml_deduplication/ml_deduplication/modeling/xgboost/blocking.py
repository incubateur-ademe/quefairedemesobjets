import logging
import resource

import duckdb
import polars as pl

logger = logging.getLogger(__name__)


def _rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024


def block_df(
    df_features: pl.DataFrame,
    additional_business_rules_sql_exprs: list[str] | None = None,
    additional_columns_to_keep: list[str] | None = None,
) -> pl.DataFrame:
    con = duckdb.connect()
    con.sql("SET memory_limit = '24GB'")
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
        (coalesce(l.acteur_type_id,-1)=coalesce(r.acteur_type_id,-1))
        OR (
            l.acteur_type_id=4 AND r.acteur_type_id=3
        )
        OR (
            l.acteur_type_id=3 AND r.acteur_type_id=4
        )
    )
    AND (
        coalesce(l.source_id,-1) <> coalesce(r.source_id,-2)
    )
"""
    if additional_business_rules_sql_exprs is not None:
        for additional_rule in additional_business_rules_sql_exprs:
            business_rules_filter_sql += f"AND ({additional_rule})"

    business_rules_filter_sql = f"({business_rules_filter_sql})"

    # On sélectionne et on optimise les types IMMÉDIATEMENT
    df_minimal = df_features.select(cols_needed).with_columns(
        [
            pl.col("latitude").cast(pl.Float32),
            pl.col("longitude").cast(pl.Float32),
        ]
    )
    con.sql("CREATE TABLE features AS SELECT * FROM df_minimal")

    # =====================================================================
    # ÉTAPE 1 : Génération de candidats sur le schéma minimal
    # =====================================================================

    # 1. SIREN
    con.sql(f"""
    CREATE table blocking_siren AS (SELECT
        l.identifiant_unique as identifiant_unique_l,
        r.identifiant_unique as identifiant_unique_r
    from features l
    inner join features r on l.siren=r.siren
    where l.identifiant_unique < r.identifiant_unique
    AND l.siren=r.siren
    AND {business_rules_filter_sql})
""")

    logger.info(
        "Blocking: siren predicate -> %s candidates ",
        con.sql("SELECT count(*) FROM blocking_siren").fetchone()[0],
    )

    # 2. Code Postal
    con.sql(f"""
        CREATE table blocking_departement AS (SELECT
            l.identifiant_unique as identifiant_unique_l,
            r.identifiant_unique as identifiant_unique_r
        from features l
        inner join features r on l.siren=r.siren
        where l.identifiant_unique < r.identifiant_unique
        AND l.code_postal[:2]=r.code_postal[:2]
        AND {business_rules_filter_sql})
    """)
    logger.info(
        "Blocking: cp predicate -> %s candidates ",
        con.sql("SELECT count(*) FROM blocking_departement").fetchone()[0],
    )

    # 3. Grille Géographique
    con.sql(f"""
            CREATE table blocking_geo AS (SELECT
                l.identifiant_unique as identifiant_unique_l,
                r.identifiant_unique as identifiant_unique_r
            from features l
            inner join features r on l.siren=r.siren
            where l.identifiant_unique < r.identifiant_unique
            AND ST_DWithin_Spheroid(
                ST_Point2D(l.latitude,l.longitude),
                ST_Point2D(r.latitude,r.longitude),
                30000
            )
            AND {business_rules_filter_sql})
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
    valid_pairs_minimal = con.sql("""
        SELECT
            identifiant_unique_l,
            identifiant_unique_r,
            ST_DISTANCE_Spheroid(
                ST_Point2D(f.latitude,f.longitude),
                ST_Point2D(f2.latitude,f2.longitude)
            ) as geo_distance
        FROM pairs p
        left join features f on p.identifiant_unique_l=f.identifiant_unique
        left join features f2 on p.identifiant_unique_l=f2.identifiant_unique
        """).pl()
    con.close()
    if valid_pairs_minimal.is_empty():
        # Retourner un dataframe vide avec le schéma attendu si aucune paire n'est trouvée
        return valid_pairs_minimal

    # On prépare les features complètes pour la jointure finale
    # On utilise left_on / right_on pour éviter les duplications de colonnes

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

    df_features = df_features.sort("identifiant_unique")
    df_features_lazy = df_features.lazy().select(column_needed_to_generate_features)

    # On n'emporte QUE les features scalaires dans la jointure à 132M lignes.
    # La colonne adresse_clean_vector (1024 x Float32) est volontairement
    # exclue ici : elle est recombinée de façon compacte dans generate_features.
    df_features_r_lazy = df_features_lazy.rename(lambda x: f"{x}_r")

    pair_ids_sorted = valid_pairs_minimal.sort(
        ["identifiant_unique_l", "identifiant_unique_r"]
    )

    # Jointure pour récupérer les features de l'entité de gauche
    df_enriched_l = (
        pair_ids_sorted.lazy()
        .select("identifiant_unique_l", "identifiant_unique_r", "geo_distance")
        .join(
            df_features_lazy.rename(lambda x: f"{x}_l"),
            left_on="identifiant_unique_l",
            right_on="identifiant_unique_l",
            how="left",
        )
        .collect(engine="streaming")
    )

    df_pairs_final = df_enriched_l.lazy().join(
        df_features_r_lazy,
        left_on="identifiant_unique_r",
        right_on="identifiant_unique_r",
        how="left",
    )

    df_pairs_final_materilized = df_pairs_final.collect(engine="streaming")
    logger.info("Finished blocking and enrichment (RSS %.0f MB).", _rss_mb())
    return df_pairs_final_materilized
