import polars as pl
import polars_distance as pld


def generate_features(
    df_pairs: pl.DataFrame,
    include_label: bool = True,
    additional_columns_to_keep: None | list[str] = None,
) -> pl.DataFrame:
    df_pairs_features = df_pairs.with_columns(
        pld.col("nom_clean_l")
        .dist_str.jaro_winkler("nom_clean_r")
        .alias("nom_clean_dist"),
        pld.col("adresse_clean_vector_l")
        .dist_arr.cosine("adresse_clean_vector_r")
        .alias("adresse_clean_distance"),
        pld.col("ville_clean_l")
        .dist_str.jaro_winkler("ville_clean_r")
        .alias("ville_clean_dist"),
        (pl.col("siren_l") == pl.col("siren_r")).alias("siren_match"),
        (pl.col("siret_l") == pl.col("siret_r")).alias("siret_match"),
        (pl.col("telephone_l") == pl.col("telephone_r")).alias("telephone_match"),
        (pl.col("code_commune_insee_l") == pl.col("code_commune_insee_r")).alias(
            "code_commune_insee_match"
        ),
        (pl.col("code_postal_l") == pl.col("code_postal_r")).alias("code_postal_match"),
        (
            pl.col("code_postal_l").str.slice(0, 2)
            == pl.col("code_postal_r").str.slice(0, 2)
        ).alias("departement_match"),
    )

    columns_to_select: list[str | pl.Expr] = [
        "identifiant_unique_l",
        "identifiant_unique_r",
        "nom_clean_dist",
        "adresse_clean_distance",
        "ville_clean_dist",
        "siren_match",
        "siret_match",
        "telephone_match",
        "code_commune_insee_match",
        "code_postal_match",
        "departement_match",
        "geo_distance",  # Computed at blocking step
        "acteur_type_id_l",
        "acteur_type_id_r",
    ]
    if include_label:
        df_pairs_features = df_pairs_features.with_columns(
            pl.coalesce(
                (pl.col("cluster_id_l") == pl.col("cluster_id_r")), False
            ).alias("label"),
        )
        columns_to_select.extend(
            [
                "label",
                pl.when("label")
                .then("cluster_id_l")
                .otherwise(None)
                .alias("cluster_id"),
            ]
        )

    if additional_columns_to_keep is not None:
        for colname in additional_columns_to_keep:
            for suffix in ["_l", "_r"]:
                colname_suffix = f"{colname}{suffix}"
                already_in_list = False
                for col in columns_to_select:
                    if isinstance(col, pl.Expr):
                        if col.meta.output_name() == colname_suffix:
                            already_in_list = True
                            break
                    else:
                        if colname_suffix == col:
                            already_in_list = True
                            break
                if not already_in_list:
                    columns_to_select.append(colname_suffix)

    df_pairs_features = df_pairs_features.select(columns_to_select)
    return df_pairs_features
