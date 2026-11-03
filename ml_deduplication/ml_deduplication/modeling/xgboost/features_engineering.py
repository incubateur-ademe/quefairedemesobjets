import duckdb


def generate_features(
    con: duckdb.DuckDBPyConnection,
    include_label: bool = True,
    additional_columns_to_keep: list[str] | None = None,
):

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
                "WHEN f.adresse_clean_vector IS NULL OR f2.adresse_clean_vector IS NULL "
                "THEN NULL "
                "ELSE 1 - list_cosine_similarity("
                "f.adresse_clean_vector, f2.adresse_clean_vector) "
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
        (
            "geo_distance",
            "ST_DISTANCE_Spheroid(ST_Point2D(f.latitude,f.longitude),ST_Point2D(f2.latitude,f2.longitude))",
        ),
    ]
    if include_label:
        feature_exprs.extend(
            [
                (
                    "label",
                    "coalesce(f.cluster_id==f2.cluster_id,false)",
                ),
                (
                    "cluster_id",
                    "CASE WHEN label THEN f.cluster_id ELSE null END",
                ),
            ],
        )

    # Colonnes `_l/_r` supplémentaires demandées (par ex. source_id, parent_id, colonnes
    # de linkage…). acteur_type_id est déjà une feature, on l'exclut.
    feature_l_names = {name for name, _ in feature_exprs}
    additional_pair_exprs = []
    if additional_columns_to_keep is not None:
        for col in additional_columns_to_keep:
            if f"{col}_l" not in feature_l_names:
                additional_pair_exprs.append(f"f.{col} AS {col}_l")
                additional_pair_exprs.append(f"f2.{col} AS {col}_r")

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
        ordered_select.append(f"    {expr_by_name[name]} AS {name},")
    if include_label:
        ordered_select.append(f"    {expr_by_name['label']} AS label,")
        ordered_select.append(f"    {expr_by_name['cluster_id']} AS cluster_id,")
    select_lines = "\n".join(
        [
            "    p.identifiant_unique_l,",
            "    p.identifiant_unique_r,",
            *ordered_select,
            *[f"    {expr}," for expr in additional_pair_exprs],
        ]
    ).rstrip(",")

    con.sql(f"""
        SET geometry_always_xy = true;
        CREATE OR REPLACE TABLE pairs_features AS
        (
            SELECT
            {select_lines}
            FROM pairs p
            left join features f on p.identifiant_unique_l=f.identifiant_unique
            left join features f2 on p.identifiant_unique_r=f2.identifiant_unique
        )
    """)

    for table in ["pairs", "features"]:
        con.sql(f"DROP TABLE IF EXISTS {table}")
    con.sql("CHECKPOINT;")
