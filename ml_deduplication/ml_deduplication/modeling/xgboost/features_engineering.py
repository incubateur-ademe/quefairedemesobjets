import numpy as np
import polars as pl
import polars_distance as pld


def _adresse_clean_distance(
    df_pairs: pl.DataFrame,
    df_embeddings: pl.DataFrame | None,
) -> pl.Expr:
    """Cosine similarity of address embeddings computed on a compact matrix.

    The 1024-dim vectors are never broadcast through the (potentially huge)
    pairs frame. Instead we build an (N x 1024) Float32 matrix from the entity
    embeddings, gather left/right rows by entity id, and compute the cosine on
    compact Float32 columns (a few hundred MB at most).
    """
    if df_embeddings is None or df_embeddings.is_empty():
        return pl.lit(None, dtype=pl.Float32).alias("adresse_clean_distance")

    embeddings = (
        df_embeddings.select("identifiant_unique", "adresse_clean_vector")
        .filter(pl.col("adresse_clean_vector").is_not_null())
        .unique(subset="identifiant_unique")
    )
    if embeddings.is_empty():
        return pl.lit(None, dtype=pl.Float32).alias("adresse_clean_distance")

    vectors = np.asarray(
        embeddings.get_column("adresse_clean_vector").to_list(), dtype=np.float32
    )  # (N, 1024)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    unit_vectors = vectors / norms

    id_to_pos = {
        eid: pos for pos, eid in enumerate(embeddings.get_column("identifiant_unique"))
    }

    def gather(id_col: str) -> np.ndarray:
        positions = np.asarray(
            [id_to_pos.get(eid, -1) for eid in df_pairs.get_column(id_col)],
            dtype=np.int64,
        )
        gathered = np.zeros((df_pairs.height, unit_vectors.shape[1]), dtype=np.float32)
        present = positions >= 0
        if present.any():
            gathered[present] = unit_vectors[positions[present]]
        return gathered

    left = gather("identifiant_unique_l")
    right = gather("identifiant_unique_r")

    # Cosine of unit vectors = dot product. polars_distance's dist_arr.cosine
    # returns a distance (1 - cosine), so we mirror that exactly.
    distance = 1.0 - np.einsum("ij,ij->i", left, right).astype(np.float32)
    known_ids = embeddings.get_column("identifiant_unique")
    valid = (
        df_pairs.get_column("identifiant_unique_l").is_in(known_ids).to_numpy()
        & df_pairs.get_column("identifiant_unique_r").is_in(known_ids).to_numpy()
    )
    distance[~valid] = np.nan

    return pl.Series("adresse_clean_distance", distance).alias("adresse_clean_distance")


def generate_features(
    df_pairs: pl.DataFrame,
    include_label: bool = True,
    additional_columns_to_keep: None | list[str] = None,
    df_embeddings: pl.DataFrame | None = None,
) -> pl.DataFrame:
    df_pairs_features = df_pairs.with_columns(
        pld.col("nom_clean_l")
        .dist_str.jaro_winkler("nom_clean_r")
        .alias("nom_clean_dist"),
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
    df_pairs_features = df_pairs_features.with_columns(
        _adresse_clean_distance(df_pairs_features, df_embeddings)
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
