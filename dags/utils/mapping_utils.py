import math
import json
import pandas as pd
from datetime import datetime


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


def flatten_ae_results(row):
    if "ae_result" in row and pd.notna(row["ae_result"]):
        ae_result = row["ae_result"]
        for key, value in ae_result.items():
            row[f"{key}"] = value
        row = row.drop(labels=["ae_result"])
    return row


def construct_url(identifiant):
    base_url = "https://quefairedemesobjets-preprod.osc-fr1.scalingo.io/admin/qfdmo/displayedacteur/{}/change/"
    return base_url.format(identifiant)


def construct_change_log(dag_run):
    change_log = {
        "message": "Acteur supprimé après vérification sur annuaire entreprise",
        "deleted_by": dag_run.run_id,
        "dag_name": dag_run.dag_id,
        "timestamp": datetime.utcnow().isoformat(),
    }

    return json.dumps(change_log, indent=2)
