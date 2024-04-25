import math


def transform_acteur_type_id(value, df_acteurtype):
    mapping_dict = {
        "solution en ligne (site web, app. mobile)": "en ligne (web, mobile)",
        "artisan, commerce indépendant": "artisan, commerce indépendant",
        "magasin / franchise,"
        " enseigne commerciale / distributeur / point de vente": "commerce",
        "point d'apport volontaire publique": "point d'apport volontaire public",
        "association, entreprise"
        " de l'économie sociale et solidaire (ess)": "Association, entreprise de l'ESS",
        "association, entreprise"
        " de l’économie sociale et solidaire (ess)": "Association, entreprise de l'ESS",
        "établissement de santé": "établissement de santé",
        "déchèterie": "déchèterie",
        "point d'apport volontaire privé": "point d'apport volontaire privé",
    }

    libelle = mapping_dict.get(value.lower())
    id_value = (
        df_acteurtype.loc[
            df_acteurtype["libelle"].str.lower() == libelle.lower(), "id"
        ].values[0]
        if any(df_acteurtype["libelle"].str.lower() == libelle.lower())
        else None
    )
    return id_value


def create_identifiant_unique(row):
    unique_str = row["identifiant_externe"].replace("/", "-")
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


def transform_float(x):
    if isinstance(x, float):
        return None if math.isnan(x) else x
    if not isinstance(x, str):
        return None
    try:
        f = float(x.replace(",", "."))
        return None if math.isnan(f) else f
    except ValueError:
        return None
