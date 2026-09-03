import logging

import polars as pl
import polars_distance as pld

logger = logging.getLogger(__name__)


def block_df(
    df_features: pl.DataFrame,
    additional_business_rules_exprs: list[pl.Expr] | None = None,
) -> pl.DataFrame:
    df_features_lazy = df_features.lazy()

    business_rules_filter_expr = [
        (
            (
                pl.col("acteur_type_id_l").fill_null(-1)
                == pl.col("acteur_type_id_r").fill_null(-1)
            )
            | ((pl.col("acteur_type_id_l") == 4) & (pl.col("acteur_type_id_r") == 3))
            | ((pl.col("acteur_type_id_l") == 3) & (pl.col("acteur_type_id_r") == 4))
        ),
        (
            pl.coalesce(pl.col("source_id_l"), pl.lit(-1))
            != pl.coalesce(pl.col("source_id_r"), pl.lit(-2))
        ),
    ]

    if additional_business_rules_exprs is not None:
        business_rules_filter_expr.extend(additional_business_rules_exprs)

    df_pairs = (
        df_features_lazy.rename(lambda x: x + "_l")
        .join(df_features_lazy.rename(lambda x: x + "_r"), how="cross")
        .with_columns(
            pl.struct("latitude_l", "longitude_l")
            .struct.rename_fields(["latitude", "longitude"])
            .alias("coords_l"),
            pl.struct("latitude_r", "longitude_r")
            .struct.rename_fields(["latitude", "longitude"])
            .alias("coords_r"),
        )
        .with_columns(
            pld.col("coords_l").dist.haversine("coords_r", "km").alias("geo_distance")
        )
        .filter(pl.col("identifiant_unique_l") < pl.col("identifiant_unique_r"))
        .filter(*business_rules_filter_expr)
        .filter(
            (
                pl.col("code_postal_l").str.slice(0, 2)
                == pl.col("code_postal_r").str.slice(0, 2)
            )
            | (pl.col("siren_l") == pl.col("siren_r"))
            | (pl.col("geo_distance") < 30)
        )
    )

    logger.info("Starting blocking...")
    df_pairs_materialized = df_pairs.collect(engine="streaming")
    logger.info("Finished blocking.")
    return df_pairs_materialized


def block_df_optimized(
    df_features: pl.DataFrame,
    additional_business_rules_exprs: list[pl.Expr] | None = None,
) -> pl.DataFrame:
    df_lazy = df_features.lazy()

    # =====================================================================
    # ÉTAPE 1 : Génération de candidats ciblée (évite le cross join O(N²))
    # =====================================================================

    # 1. Candidats par SIREN (Match exact)
    candidates_siren = df_lazy.join(
        df_lazy, on="siren", how="inner", suffix="_r"
    ).filter(pl.col("identifiant_unique") < pl.col("identifiant_unique_r"))

    # 2. Candidats par Code Postal (2 premiers caractères)
    df_cp = df_lazy.with_columns(
        pl.col("code_postal").str.slice(0, 2).alias("cp_prefix")
    )
    candidates_cp = df_cp.join(df_cp, on="cp_prefix", how="inner", suffix="_r").filter(
        pl.col("identifiant_unique") < pl.col("identifiant_unique_r")
    )

    # 3. Candidats par Grille Géographique (Approximation spatiale)
    # Astuce : On arrondit les coordonnées pour créer des "buckets" (grilles).
    # 0.5 degré ~= 50 km. Cela garantit de capturer les paires à < 30 km
    # tout en évitant les effets de bord des grilles trop fines.
    df_geo = df_lazy.with_columns(
        [
            (pl.col("latitude") / 0.5).floor().alias("lat_grid"),
            (pl.col("longitude") / 0.5).floor().alias("lon_grid"),
        ]
    )
    candidates_geo = df_geo.join(
        df_geo, on=["lat_grid", "lon_grid"], how="inner", suffix="_r"
    ).filter(pl.col("identifiant_unique") < pl.col("identifiant_unique_r"))

    # =====================================================================
    # ÉTAPE 2 : Union et dédoublonnage des candidats
    # =====================================================================
    # On combine les 3 sources. Une paire peut apparaître plusieurs fois
    # (ex: même SIREN et même CP), on la dédoublonne immédiatement.
    candidates = pl.concat(
        [candidates_siren, candidates_cp, candidates_geo], how="vertical"
    ).unique(subset=["identifiant_unique", "identifiant_unique_r"])

    # =====================================================================
    # ÉTAPE 3 : Application des règles métier et calculs coûteux
    # =====================================================================
    # Le dataset est maintenant réduit de ~10 milliards à quelques millions
    # de lignes maximum. Le calcul de Haversine est désormais trivial.

    business_rules_filter_expr = [
        (
            (
                pl.col("acteur_type_id").fill_null(-1)
                == pl.col("acteur_type_id_r").fill_null(-1)
            )
            | ((pl.col("acteur_type_id") == 4) & (pl.col("acteur_type_id_r") == 3))
            | ((pl.col("acteur_type_id") == 3) & (pl.col("acteur_type_id_r") == 4))
        ),
        (
            pl.coalesce(pl.col("source_id"), pl.lit(-1))
            != pl.coalesce(pl.col("source_id_r"), pl.lit(-2))
        ),
    ]

    if additional_business_rules_exprs is not None:
        business_rules_filter_expr.extend(additional_business_rules_exprs)

    df_pairs = (
        candidates.with_columns(
            [
                pl.struct("latitude", "longitude").alias("coords_l"),
                pl.struct("latitude_r", "longitude_r").alias("coords_r"),
            ]
        )
        .with_columns(
            [pld.col("coords_l").dist.haversine("coords_r", "km").alias("geo_distance")]
        )
        .filter(*business_rules_filter_expr)
    )

    logger.info("Starting blocking on optimized candidates...")
    df_pairs_materialized = df_pairs.collect(engine="streaming")
    logger.info(f"Finished blocking. Generated {df_pairs_materialized.height} pairs.")

    return df_pairs_materialized
