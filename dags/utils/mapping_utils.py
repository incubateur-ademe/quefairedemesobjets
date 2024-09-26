import json
import math
import re
from datetime import datetime
from importlib import import_module
from pathlib import Path

import numpy as np
import pandas as pd

env = Path(__file__).parent.parent.name

utils = import_module(f"{env}.utils.utils")


def process_siret(siret):
    if pd.isna(siret):
        return None
    siret = str(siret).replace(" ", "")

    if not siret.isdigit():
        return None

    if len(siret) == 9:
        return siret

    if len(siret) == 13:
        return "0" + siret

    if len(siret) == 14:
        return siret

    return None


def process_phone_number(number):
    if pd.isna(number):
        return number

    number = re.sub(r"[^\d+]", "", number)

    if number.startswith("33"):
        number = "0" + number[2:]

    if len(number) < 6:
        return None

    return number


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
        "plateforme inertes": "plateforme de valorisation des inertes",
        "magasin / franchise, enseigne commerciale / distributeur / point de vente "
        "/ franchise, enseigne commerciale / distributeur / point de vente": "commerce",
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


def create_identifiant_unique(row, source_name=None):
    unique_str = row["identifiant_externe"].replace("/", "-")
    if (
        row.get("type_de_point_de_collecte")
        == "Solution en ligne (site web, app. mobile)"
    ):
        unique_str = unique_str + "_d"
    return row.get("ecoorganisme", source_name).lower() + "_" + unique_str


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


def process_reparacteurs(df, df_sources, df_acteurtype):
    df["produitsdechets_acceptes"] = df.apply(combine_categories, axis=1)
    df["source_id"] = get_id_from_code(
        "CMA - Chambre des métiers et de l'artisanat", df_sources
    )
    # TODO : on pourrait gérer en configuration les colonne qui sont pareil pour tous
    df["label_code"] = "reparacteur"
    df["latitude"] = df["latitude"].apply(clean_float_from_fr_str)
    df["longitude"] = df["longitude"].apply(clean_float_from_fr_str)
    df["type_de_point_de_collecte"] = None
    df["acteur_type_id"] = transform_acteur_type_id(
        "artisan, commerce indépendant", df_acteurtype=df_acteurtype
    )
    # TODO : voir si on peut tester les urls dans un opérateur, quite à maintenir
    # un cache des urls validées
    df["website"] = df["website"].apply(prefix_url)
    df["point_de_reparation"] = True
    return df


def process_actors(df):
    df["nom_de_lorganisme_std"] = df["nom_de_lorganisme"].str.replace("-", "")
    df["id_point_apport_ou_reparation"] = df["id_point_apport_ou_reparation"].fillna(
        df["nom_de_lorganisme_std"]
    )
    df["id_point_apport_ou_reparation"] = (
        df["id_point_apport_ou_reparation"]
        .str.replace(" ", "_")
        .str.replace("_-", "_")
        .str.replace("__", "_")
    )
    df = df.rename(columns={"latitudewgs84": "latitude", "longitudewgs84": "longitude"})
    if "latitude" in df.columns and "longitude" in df.columns:
        df = df.dropna(subset=["latitude", "longitude"])
        df["latitude"] = df["latitude"].astype(float).replace({np.nan: None})
        df["longitude"] = df["longitude"].astype(float).replace({np.nan: None})
    if "service_a_domicile" in df.columns:
        df.loc[
            df["service_a_domicile"] == "service à domicile uniquement", "statut"
        ] = "SUPPRIME"
    if "site_web" in df.columns:
        df["site_web"] = df["site_web"].apply(prefix_url)
    return df


def clean_float_from_fr_str(value):
    if isinstance(value, str):
        value = re.sub(r",$", "", value).replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None


def combine_categories(row):
    categories = [row["categorie"], row["categorie2"], row["categorie3"]]
    categories = [cat for cat in categories if pd.notna(cat)]
    return " | ".join(categories)


def prefix_url(url):
    if pd.isna(url):
        return None
    url = str(url)

    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    return url


def combine_comments(existing_commentaires, new_commentaires):
    def parse_json_or_default(json_str, default):
        try:
            parsed_json = json.loads(json_str)
            return parsed_json if isinstance(parsed_json, list) else [default]
        except (json.JSONDecodeError, TypeError):
            return [default]

    existing_commentaires_json = (
        parse_json_or_default(existing_commentaires, {"message": existing_commentaires})
        if existing_commentaires
        else []
    )

    if new_commentaires:
        try:
            new_commentaires_json = json.loads(new_commentaires)
            if not isinstance(new_commentaires_json, dict):
                raise ValueError("New commentaires should be a JSON object")
            new_commentaires_json = [new_commentaires_json]
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError("New commentaires should be a valid JSON object") from e
    else:
        new_commentaires_json = []

    combined_commentaires = existing_commentaires_json + new_commentaires_json
    return json.dumps(combined_commentaires)


def create_full_adresse(df):
    return (
        df["adresse"]
        .fillna("")
        .str.cat(df["code_postal"].fillna(""), sep=" ")
        .str.cat(df["ville"].fillna(""), sep=" ")
    )


def replace_with_selected_candidat(row):
    row["adresse_candidat"] = None
    if "ae_result" in row:
        ae_result = row["ae_result"]
        best_candidat_index = row.get("best_candidat_index", None)
        if best_candidat_index is not None and pd.notna(best_candidat_index):
            selected_candidat = ae_result[int(best_candidat_index) - 1]
            row["statut"] = "ACTIF"
            row["adresse_candidat"] = selected_candidat.get("adresse_candidat")
            row["siret"] = selected_candidat.get("siret_candidat")
            row["nom"] = selected_candidat.get("nom_candidat")
            row["location"] = selected_candidat.get("location_candidat")
            row["commentaires"] = construct_change_log(
                "Actor replaced after verification on annuaire entreprise"
            )
        else:
            row["statut"] = "SUPPRIME"
            row["adresse_candidat"] = None
            row["siret"] = None
            row["nom"] = None
            row["location"] = None
            row["commentaires"] = construct_change_log(
                "Actor removed after verification on annuaire entreprise"
            )

        row = row.drop(labels=["ae_result"])

    return row


def construct_url(identifiant, env):
    if env == "production":
        base_url = "https://lvao.ademe.fr/admin/qfdmo/displayedacteur/{}/change/"
    else:
        base_url = "https://quefairedemesobjets-preprod.osc-fr1.scalingo.io/admin/qfdmo/displayedacteur/{}/change/"
    return base_url.format(identifiant)


def construct_change_log(message):
    change_log = {
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }

    return json.dumps(change_log, indent=2)
