import json
import math
import re
from datetime import datetime
from typing import Any

import pandas as pd
from sources.config import shared_constants as constants
from utils.formatter import format_libelle_to_code


def _clean_number(number: Any) -> str | None:
    if pd.isna(number) or number is None:
        return None

    # suppression des 2 derniers chiffres si le caractère si == .0
    number = re.sub(r"\.0$", "", str(number))
    # suppression de tous les caractères autre que digital
    number = re.sub(r"[^\d+]", "", number)
    return number


def process_siret(siret):
    siret = _clean_number(siret)

    if siret is None:
        return None

    if len(siret) == 9:
        return siret

    if len(siret) == 13:
        return "0" + siret

    if len(siret) == 14:
        return siret

    return None


def process_phone_number(number, code_postal):

    number = _clean_number(number)

    if number is None:
        return None

    if len(number) == 9 and code_postal and int(code_postal) < 96000:
        number = "0" + number

    if number.startswith("33"):
        number = "0" + number[2:]

    if len(number) < 5:
        return None

    return number


# TODO : Ajout de tests unitaires
def transform_acteur_type_id(value, acteurtype_id_by_code):
    mapping_dict = {
        # Here we store key without accents and special characters
        "solution en ligne (site web, app. mobile)": "acteur_digital",
        "artisan, commerce independant": "artisan",
        "magasin / franchise,"
        " enseigne commerciale / distributeur / point de vente": "commerce",
        "point d'apport volontaire publique": "pav_public",
        "association, entreprise de l'economie sociale et solidaire (ess)": "ess",
        "etablissement de sante": "ets_sante",
        "decheterie": "decheterie",
        "pharmacie": "commerce",
        "point d'apport volontaire prive": "pav_prive",
        "plateforme inertes": "plateforme_inertes",
        "magasin / franchise, enseigne commerciale / distributeur / point de vente "
        "/ franchise, enseigne commerciale / distributeur / point de vente": "commerce",
        "point d'apport volontaire ephemere / ponctuel": "pav_ponctuel",
    }
    code = mapping_dict.get(format_libelle_to_code(value), None)
    if code is None:
        raise ValueError(f"Acteur type `{value}` not found in mapping")
    if code in acteurtype_id_by_code.keys():
        return acteurtype_id_by_code[code]
    else:
        raise ValueError(f"Acteur type {code.lower()} not found in database")


def get_id_from_code(code, df_mapping):
    if any(df_mapping["code"].str.lower() == code.lower()):
        id_value = df_mapping.loc[
            df_mapping["code"].str.lower() == code.lower(), "id"
        ].values[0]
        return id_value
    else:
        raise ValueError(f"{code.lower()} not found in database")


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


def parse_float(value):
    if isinstance(value, float):
        return None if math.isnan(value) else value
    if not isinstance(value, str):
        return None
    value = re.sub(r",$", "", value).replace(",", ".")
    try:
        f = float(value)
        return None if math.isnan(f) else f
    except ValueError:
        return None


def combine_categories(row, combine_columns_categories):
    categories = [row[col] for col in combine_columns_categories if pd.notna(row[col])]
    return " | ".join(categories)


# DEPRECATED
def prefix_url(url) -> str:
    if pd.isna(url):
        return ""
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
            row["statut"] = constants.ACTEUR_ACTIF
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


def construct_change_log(message):
    change_log = {
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }

    return json.dumps(change_log, indent=2)
