import logging

import polars as pl
import polars_distance as pld

logger = logging.getLogger(__name__)


def block_df_old(
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


def block_df(
    df_features: pl.DataFrame,
    additional_business_rules_exprs: list[pl.Expr] | None = None,
    additional_columns_to_keep: list[str] | None = None,
) -> pl.DataFrame:
    # =====================================================================
    # ÉTAPE 0 : Définition du schéma minimal et optimisation des types
    # =====================================================================
    cols_needed = [
        "identifiant_unique",
        "siren",
        "code_postal",
        "latitude",
        "longitude",
        "source_id",
        "acteur_type_id",
    ]
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
        for expr in additional_business_rules_exprs:
            root_names = expr.meta.root_names()
            cols_needed.append(root_names[0].removesuffix("_l"))

    # On sélectionne et on optimise les types IMMÉDIATEMENT
    df_minimal = (
        df_features.select(cols_needed)
        .with_columns(
            [
                pl.col("latitude").cast(pl.Float32),
                pl.col("longitude").cast(pl.Float32),
                # Si vos IDs sont numériques, décommentez la ligne suivante pour gagner encore plus de mémoire :
                # pl.col("identifiant_unique").cast(pl.Int32),
            ]
        )
        .lazy()
    )

    # Préparation des versions _l et _r du dataset minimal
    df_l = df_minimal.rename(lambda x: f"{x}_l")
    df_r = df_minimal.rename(lambda x: f"{x}_r")

    # =====================================================================
    # ÉTAPE 1 : Génération de candidats sur le schéma minimal
    # =====================================================================

    # 1. SIREN
    candidates_siren = df_l.join(
        df_r, left_on="siren_l", right_on="siren_r", how="inner", coalesce=False
    ).filter(pl.col("identifiant_unique_l") < pl.col("identifiant_unique_r"))

    # 2. Code Postal
    df_cp_l = df_l.with_columns(
        pl.col("code_postal_l").str.slice(0, 2).alias("cp_prefix_l")
    )
    df_cp_r = df_r.with_columns(
        pl.col("code_postal_r").str.slice(0, 2).alias("cp_prefix_r")
    )
    candidates_cp = (
        df_cp_l.join(
            df_cp_r, left_on="cp_prefix_l", right_on="cp_prefix_r", how="inner"
        )
        .filter(pl.col("identifiant_unique_l") < pl.col("identifiant_unique_r"))
        .drop("cp_prefix_l")
    )

    # 3. Grille Géographique
    df_geo_l = df_l.with_columns(
        [
            (pl.col("latitude_l") / 0.5).floor().alias("lat_grid_l"),
            (pl.col("longitude_l") / 0.5).floor().alias("lon_grid_l"),
        ]
    )
    df_geo_r = df_r.with_columns(
        [
            (pl.col("latitude_r") / 0.5).floor().alias("lat_grid_r"),
            (pl.col("longitude_r") / 0.5).floor().alias("lon_grid_r"),
        ]
    )
    candidates_geo = (
        df_geo_l.join(
            df_geo_r,
            left_on=["lat_grid_l", "lon_grid_l"],
            right_on=["lat_grid_r", "lon_grid_r"],
            how="inner",
        )
        .filter(pl.col("identifiant_unique_l") < pl.col("identifiant_unique_r"))
        .drop("lat_grid_l", "lon_grid_l")
    )

    # =====================================================================
    # ÉTAPE 2 : Union, dédoublonnage et règles métier (Toujours en minimal)
    # =====================================================================
    candidates = pl.concat(
        [candidates_siren, candidates_cp, candidates_geo], how="vertical"
    ).unique(subset=["identifiant_unique_l", "identifiant_unique_r"])

    # Calcul de la distance uniquement sur le dataset déjà réduit et minimal
    df_pairs_minimal = (
        candidates.with_columns(
            [
                pl.struct("latitude_l", "longitude_l")
                .struct.rename_fields(["latitude", "longitude"])
                .alias("coords_l"),
                pl.struct("latitude_r", "longitude_r")
                .struct.rename_fields(["latitude", "longitude"])
                .alias("coords_r"),
            ]
        )
        .with_columns(
            [pld.col("coords_l").dist.haversine("coords_r", "km").alias("geo_distance")]
        )
        .filter(pl.col("geo_distance") < 30)  # Règle de distance
        .filter(*business_rules_filter_expr)
    )

    # =====================================================================
    # ÉTAPE 3 : Collecte intermédiaire et Jointure finale (Le secret anti-OOM)
    # =====================================================================
    logger.info("Collecting minimal valid pairs to free memory...")
    # On matérialise SEULEMENT les paires valides avec le schéma minimal.
    # C'est très léger en RAM.
    valid_pairs_minimal = df_pairs_minimal.collect(engine="streaming")

    logger.info(
        f"Found {valid_pairs_minimal.height} valid candidate pairs. Enriching with full features..."
    )

    if valid_pairs_minimal.is_empty():
        # Retourner un dataframe vide avec le schéma attendu si aucune paire n'est trouvée
        return valid_pairs_minimal

    # On prépare les features complètes pour la jointure finale
    # On utilise left_on / right_on pour éviter les duplications de colonnes

    column_needed_to_generate_features = [
        "identifiant_unique",
        "nom_clean",
        "adresse_clean_vector",
        "ville_clean",
        "siren",
        "siret",
        "telephone",
        "code_commune_insee",
        "code_postal",
    ]
    if additional_columns_to_keep is not None:
        column_needed_to_generate_features.extend(additional_columns_to_keep)
        column_needed_to_generate_features = list(
            set(column_needed_to_generate_features)
        )

    df_features_lazy = df_features.lazy().select(column_needed_to_generate_features)

    # Jointure pour récupérer les features de l'entité de gauche
    df_enriched_l = (
        valid_pairs_minimal.lazy()
        .sort("identifiant_unique_l")
        .select("identifiant_unique_l", "identifiant_unique_r", "geo_distance")
        .join(
            df_features_lazy.rename(lambda x: f"{x}_l").sort("identifiant_unique_l"),
            left_on="identifiant_unique_l",
            right_on="identifiant_unique_l",
            how="left",
        )
    )

    df_features_r_lazy = df_features.lazy().rename(lambda x: f"{x}_r")

    df_pairs_final = df_enriched_l.sort("identifiant_unique_r").join(
        df_features_r_lazy.sort("identifiant_unique_r"),
        left_on="identifiant_unique_r",
        right_on="identifiant_unique_r",
        how="left",
    )
    logger.info("Starting blocking and enrichment.")
    df_pairs_final_materilized = df_pairs_final.collect(engine="streaming")
    logger.info("Finished blocking and enrichment.")
    return df_pairs_final_materilized
