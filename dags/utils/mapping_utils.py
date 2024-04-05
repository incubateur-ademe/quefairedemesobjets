def transform_acteur_type_id(value, df_acteurtype):
    mapping_dict = {
        "Solution en ligne (site web, app. mobile)": "en ligne (web, mobile)",
        "Artisan, commerce indépendant": "artisan, commerce indépendant",
        "Magasin / Franchise, Enseigne commerciale / Distributeur / Point de vente": (
            "commerce"
        ),
        "Point d'Apport Volontaire Publique": "point d'apport volontaire public",
        "Association, entreprise de l’économie sociale et solidaire (ESS)": (
            "Association, entreprise de l'ESS"
        ),
        "Déchèterie": "déchèterie",
    }
    libelle = mapping_dict.get(value)
    id_value = (
        df_acteurtype.loc[df_acteurtype["libelle"] == libelle, "id"].values[0]
        if any(df_acteurtype["libelle"] == libelle)
        else None
    )
    return id_value


def create_identifiant_unique(row):
    unique_str = row["identifiant_externe"]
    if row["type_de_point_de_collecte"] == "Solution en ligne (site web, app. mobile)":
        unique_str = unique_str + "_d"
    return row["ecoorganisme"].lower() + "_" + unique_str


def get_id_from_code(value, df_mapping, code="code"):
    id_value = (
        df_mapping.loc[df_mapping[code].str.lower() == value.lower(), "id"].values[0]
        if any(df_mapping[code].str.lower() == value.lower())
        else None
    )
    return id_value
