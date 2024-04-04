import hashlib


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
    nom_affiche = mapping_dict.get(value)
    id_value = (
        df_acteurtype.loc[df_acteurtype["nom_affiche"] == nom_affiche, "id"].values[0]
        if any(df_acteurtype["nom_affiche"] == nom_affiche)
        else None
    )
    return id_value


def generate_unique_id(row, selected_columns):
    unique_str = "_".join([str(row[col]) for col in selected_columns])
    return (
        str(row["nom"].replace(" ", "_").lower())
        + "_"
        + hashlib.sha256(unique_str.encode()).hexdigest()
    )


def create_identifiant_unique(row):
    unique_str = row["identifiant_externe"].lower()
    if row["service_a_domicile"] == "service à domicile uniquement":
        unique_str = unique_str + "_d"
    return unique_str


def get_id_from_code(value, df_mapping, code="nom"):
    id_value = (
        df_mapping.loc[df_mapping[code].str.lower() == value.lower(), "id"].values[0]
        if any(df_mapping[code].str.lower() == value.lower())
        else None
    )
    return id_value
