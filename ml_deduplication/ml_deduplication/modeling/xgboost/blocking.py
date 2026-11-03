import logging
import resource
import sys

import duckdb

logger = logging.getLogger(__name__)


def _rss_mb() -> float:
    """Return the current peak resident set size in MB.

    ``ru_maxrss`` is reported in bytes on macOS but in kilobytes on Linux, so the
    unit must be converted per-platform for the log to be meaningful.
    """
    ru_maxrss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return ru_maxrss / 1024 / 1024
    return ru_maxrss / 1024


def run_blocking(
    con: duckdb.DuckDBPyConnection,
    additional_business_rules_sql_exprs: list[str] | None = None,
) -> int:
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
    # =====================================================================
    # ÉTAPE 1 : Génération de candidats sur le schéma minimal
    # =====================================================================

    # 1. Code Postal
    con.sql(f"""
    CREATE OR REPLACE table blocking_departement AS (
        with joined as (
            SELECT
                columns(l.*) as '\\0_l',
                columns(r.*) as '\\0_r',
            from
                features_minimal l
            inner join features_minimal r on
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
        con.sql("SELECT count(*) FROM blocking_departement").limit(1).fetchall()[0][0],
    )

    # 2. Grille Géographique optimisée en jointure grace à ST_DWITHIN (distance en degré, 0.14 correspond à 15km)
    con.sql("""
    CREATE OR REPLACE table blocking_geo_temp AS (
        SELECT
            columns(l.*) as '\\0_l',
            columns(r.*) as '\\0_r'
        from
            features_minimal l
        inner join features_minimal r on
            ST_DWithin(
                l.location,
                r.location,
                0.14
            )
    )
    """)

    con.sql(f"""
    CREATE OR REPLACE table blocking_geo AS (
        SELECT
            identifiant_unique_l,
            identifiant_unique_r
        from blocking_geo_temp
        anti join blocking_departement using (identifiant_unique_l, identifiant_unique_r)
        where identifiant_unique_l < identifiant_unique_r
        AND {business_rules_filter_sql}
    )
    """)

    logger.info(
        "Blocking: geo predicate -> %s candidates",
        con.sql("SELECT count(*) FROM blocking_geo").limit(1).fetchall()[0][0],
    )

    # 3. SIREN
    con.sql(f"""
    CREATE OR REPLACE table blocking_siren AS (
        with joined as (
            SELECT
                columns(l.*) as '\\0_l',
                columns(r.*) as '\\0_r',
            from
                features_minimal l
            inner join features_minimal r on
                l.siren=r.siren
        )
        SELECT
            identifiant_unique_l,
            identifiant_unique_r
        from joined
        anti join blocking_departement using (identifiant_unique_l, identifiant_unique_r)
        anti join blocking_geo using (identifiant_unique_l, identifiant_unique_r)
        where identifiant_unique_l < identifiant_unique_r
        AND {business_rules_filter_sql}

    )
    """)

    logger.info(
        "Blocking: siren predicate -> %s candidates ",
        con.sql("SELECT count(*) FROM blocking_siren").limit(1).fetchall()[0][0],
    )

    # =====================================================================
    # ÉTAPE 3 : Union
    # =====================================================================
    # Les trois prédicats ont été réduits et dédoublonnés (distance + règles
    # métier), donc la concaténation ne fait pas exploser la mémoire.
    logger.info("Collecting minimal valid pairs to free memory...")
    con.sql("""
        CREATE OR REPLACE TABLE pairs AS
        SELECT identifiant_unique_l, identifiant_unique_r, 'siren'      AS blocking_origin FROM blocking_siren
        UNION ALL
        SELECT identifiant_unique_l, identifiant_unique_r, 'departement' AS blocking_origin FROM blocking_departement
        UNION ALL
        SELECT identifiant_unique_l, identifiant_unique_r, 'geo'         AS blocking_origin FROM blocking_geo
        """)

    num_candidates: int = (
        con.sql("SELECT count(*) FROM pairs").limit(1).fetchall()[0][0]
    )
    logger.info("Blocking: dedup complete -> %s valid candidate pairs ", num_candidates)
    con.sql("CHECKPOINT;")
    for table in [
        "blocking_siren",
        "blocking_departement",
        "blocking_geo",
        "blocking_geo_temp",
    ]:
        con.sql(f"DROP TABLE IF EXISTS {table}")
    con.sql("CHECKPOINT;")

    return num_candidates
