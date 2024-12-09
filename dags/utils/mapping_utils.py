import json
import math
import re
from datetime import datetime
from typing import Any, Dict, List, Pattern, Tuple

import pandas as pd
from utils.formatter import format_libelle_to_code


def _clean_number(number: Any) -> str | None:
    # On met les évaluations les moints couteuses en premier
    if number is None or pd.isna(number):
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


ACTEUR_TYPE_MAPPING_STATIC = {
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

# Voir décision https://www.notion.so/accelerateur-transition-ecologique-ademe/Mapper-les-codes-acteur-type-source-dynamiquement-1576523d57d7803b9a98c146730088c5
# On sort de la fonction transform_acteur_type_id pour éviter
# d'avoir à compiler les patterns à chaque appel
ACTEUR_TYPE_MAPPING_DYNAMIC: List[Tuple[Pattern[str], str]] = [
    (re.compile("hospitalier|clinique|medical", flags=re.IGNORECASE), "ets_sante"),
    (re.compile(r"association", flags=re.IGNORECASE), "ess"),
    (
        re.compile(r"collectivite|mairie|ministere", flags=re.IGNORECASE),
        "collectivite",
    ),
]


# TODO : Ajout de tests unitaires
def transform_acteur_type_id(
    value: str, acteurtype_id_by_code: Dict[str, int], stop_on_error: bool = True
) -> int | None:
    """Converti un libellé d'acteur type en son id correspondant

    Args:
        value (str): Libellé de l'acteur type de la source
        acteurtype_id_by_code (dict): Dictionnaire de correspondance code -> id DB
        stop_on_error (bool, optional): Si True, lève une exception si
            le libellé n'est pas trouvé. Permets d'utiliser la fonction dans des
            normalisation custom de certaines sources. On essaye au mieux
            (avec stop_on_error=False) et on renormalise par dessus.

    Returns:
        int: Id de l'acteur type correspondant
    """
    value = format_libelle_to_code(value)

    # On essaye de trouver le code selon l'ordre suivant:
    # 1) On essaye dans nos codes DB
    code = value if value in acteurtype_id_by_code.keys() else None

    # 2) Sinon on essaye notre mapping statique
    if code is None:
        code = ACTEUR_TYPE_MAPPING_STATIC.get(value, None)

    # 3) Sinon on essaye notre mapping dynamique
    if code is None:
        code = next(
            (
                code
                for pattern, code in ACTEUR_TYPE_MAPPING_DYNAMIC
                if re.search(pattern, value)
            ),
            None,
        )

    if code is None and stop_on_error:
        raise ValueError(
            f"Libellé acteur type `{value}` pas trouvé (ni DB ni mappings)"
        )

    return acteurtype_id_by_code.get(code, None)


def create_identifiant_unique(row):
    unique_str = row["identifiant_externe"].replace("/", "-")
    if (
        row.get("type_de_point_de_collecte")
        == "Solution en ligne (site web, app. mobile)"
    ):
        unique_str = unique_str + "_d"
    return row.get("source_code").lower() + "_" + unique_str


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


def construct_change_log(message):
    change_log = {
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
    }

    return json.dumps(change_log, indent=2)
