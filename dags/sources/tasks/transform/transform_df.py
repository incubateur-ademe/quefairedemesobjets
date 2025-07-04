import logging
import math
import re

import pandas as pd
import requests
from fuzzywuzzy import fuzz
from shapely import wkb
from shapely.geometry import Point
from sources.tasks.airflow_logic.config_management import DAGConfig
from sources.tasks.transform.transform_column import (
    clean_code_postal,
    clean_number,
    clean_siren,
    clean_siret,
)

from utils import logging_utils as log
from utils.formatter import format_libelle_to_code

logger = logging.getLogger(__name__)

ACTEUR_TYPE_DIGITAL = "acteur_digital"
ACTEUR_TYPE_ESS = "ess"
LABEL_ESS = "ess"
LABEL_TO_IGNORE = ["non applicable", "na", "n/a", "null", "aucun", "non"]
MANDATORY_COLUMNS_AFTER_NORMALISATION = [
    "identifiant_unique",
    "identifiant_externe",
    "nom",
    "acteur_service_codes",
    "label_codes",
    "proposition_service_codes",
    "source_code",
    "acteur_type_code",
    "statut",
]
REGEX_BAN_SEPARATORS = r"\s,;-"
STRIP_BAN = REGEX_BAN_SEPARATORS.replace("\\s", " ")


def merge_duplicates(
    df: pd.DataFrame,
    group_column: str,
    merge_as_list_columns: list,
    merge_as_proposition_service_columns: list,
) -> pd.DataFrame:

    for col in merge_as_list_columns + merge_as_proposition_service_columns:
        if col not in df.columns:
            raise ValueError(f"Column {col} not found in DataFrame")

    df_duplicates = df[df.duplicated(group_column, keep=False)]
    identifiant_uniques = df_duplicates["identifiant_unique"].unique()
    if df_duplicates.empty:
        logger.warning("No duplicate found")
        return df
    log.preview(f"{len(identifiant_uniques)} duplicates found", identifiant_uniques)

    df_non_duplicates = df[~df.duplicated(group_column, keep=False)]

    merge_as_first_columns = [
        col
        for col in df.columns
        if col
        not in merge_as_list_columns
        + merge_as_proposition_service_columns
        + [group_column]
    ]
    df_merged_duplicates = (
        df_duplicates.groupby(group_column)
        .agg(
            {
                **{col: "first" for col in merge_as_first_columns},
                **{col: _merge_list_columns for col in merge_as_list_columns},
                **{
                    col: _merge_proposition_service_columns
                    for col in merge_as_proposition_service_columns
                },
            }
        )
        .reset_index()
    )

    df_final = pd.concat([df_non_duplicates, df_merged_duplicates], ignore_index=True)

    return df_final


def _merge_list_columns(group):
    result_sets = set()
    for result in group:
        result_sets.update(result)
    return sorted(list(result_sets))


def _merge_proposition_service_columns(group):
    sscat_by_action = {}
    for pss in group:
        for ps in pss:
            if ps["action"] not in sscat_by_action:
                sscat_by_action[ps["action"]] = []
            sscat_by_action[ps["action"]].extend(ps["sous_categories"])

    # sort sscat_by_action by action code
    return [
        {
            "action": action,
            "sous_categories": sorted(list(set(sscat_by_action[action]))),
        }
        for action in sorted(sscat_by_action.keys())
    ]


def clean_telephone(row: pd.Series, _):
    telephone_column = list(row.keys())[0]
    number = clean_number(row[telephone_column])

    if number is None:
        row[["telephone"]] = ""
        return row[["telephone"]]

    if len(number) == 9 and row["code_postal"] and int(row["code_postal"]) < 96000:
        number = "0" + number

    if number.startswith("33"):
        number = "0" + number[2:]

    if len(number) < 6:
        number = ""

    row["telephone"] = number
    return row[["telephone"]]


def clean_siret_and_siren(row, _):
    if "siret" in row:
        row["siret"] = clean_siret(row["siret"])
    else:
        row["siret"] = ""
    if "siren" in row and row["siren"]:
        row["siren"] = clean_siren(row["siren"])
    else:
        row["siren"] = (
            row["siret"][:9] if "siret" in row and row["siret"] is not None else ""
        )
    return row[["siret", "siren"]]


def clean_identifiant_externe(row, _):
    # nom de la première colonne
    identifiant_externe_column = list(row.keys())[0]
    if not row[identifiant_externe_column] and "nom" in row:
        if not row["nom"]:
            raise ValueError(
                f"{identifiant_externe_column} or nom is required to generate"
                " identifiant_externe"
            )
        row[identifiant_externe_column] = (
            row["nom"].replace("-", "").replace(" ", "_").replace("__", "_")
        )
    row["identifiant_externe"] = str(row[identifiant_externe_column]).strip()

    if "acteur_type_code" in row and row["acteur_type_code"] == ACTEUR_TYPE_DIGITAL:
        row["identifiant_externe"] += "_d"

    return row[["identifiant_externe"]]


def compute_identifiant_unique(identifiant_externe, source_code):
    unique_str = str(identifiant_externe).replace("/", "-").strip()
    return source_code.lower() + "_" + unique_str


def clean_identifiant_unique(row, _):
    if not row.get("identifiant_externe"):
        raise ValueError(
            "identifiant_externe is required to generate identifiant_unique"
        )
    row["identifiant_unique"] = compute_identifiant_unique(
        row["identifiant_externe"], row["source_code"]
    )
    return row[["identifiant_unique"]]


def merge_sous_categories_columns(row, _):
    categories = [row[col] for col in row.keys() if pd.notna(row[col]) and row[col]]
    row["produitsdechets_acceptes"] = " | ".join(categories)
    return row[["produitsdechets_acceptes"]]


def clean_adresse(row, dag_config):
    row["adresse"] = row["adresse_format_ban"]
    address = postal_code = city = ""
    if dag_config.validate_address_with_ban:
        address, postal_code, city = _get_address(row["adresse_format_ban"])
    else:
        address, postal_code, city = _extract_details(row["adresse_format_ban"])
    row["adresse"] = address
    row["code_postal"] = postal_code
    row["ville"] = city
    return row[["adresse", "code_postal", "ville"]]


def clean_acteur_service_codes(row, _):
    acteur_service_codes = []
    if row.get("point_dapport_de_service_reparation") or row.get("point_de_reparation"):
        acteur_service_codes.append("service_de_reparation")
    if row.get("point_dapport_pour_reemploi") or row.get(
        "point_de_collecte_ou_de_reprise_des_dechets"
    ):
        acteur_service_codes.append("structure_de_collecte")
    row["acteur_service_codes"] = acteur_service_codes
    return row[["acteur_service_codes"]]


def clean_action_codes(row, dag_config: DAGConfig):
    action_codes = []
    if row.get("point_dapport_de_service_reparation") or row.get("point_de_reparation"):
        action_codes.append("reparer")
    if row.get("point_dapport_pour_reemploi"):
        if dag_config.returnable_objects:
            action_codes.append("rapporter")
        else:
            action_codes.append("donner")
    if row.get("point_de_collecte_ou_de_reprise_des_dechets"):
        action_codes.append("trier")
    row["action_codes"] = action_codes
    return row[["action_codes"]]


def clean_label_codes(row, dag_config):
    label_column = row.keys()[0]
    label_codes = []

    if row["acteur_type_code"] == ACTEUR_TYPE_ESS:
        label_codes.append(LABEL_ESS)

    labels_etou_bonus = row.get(label_column) or ""

    if (
        dag_config.label_bonus_reparation
        and "Agréé Bonus Réparation" in labels_etou_bonus
    ):
        label_codes.append(dag_config.label_bonus_reparation)
        labels_etou_bonus = labels_etou_bonus.replace("Agréé Bonus Réparation", "")

    for label_ou_bonus in labels_etou_bonus.split("|"):
        label_ou_bonus = format_libelle_to_code(label_ou_bonus)
        if label_ou_bonus in LABEL_TO_IGNORE or not label_ou_bonus:
            continue
        label_codes.append(label_ou_bonus)

    row["label_codes"] = label_codes
    return row[["label_codes"]]


def get_latlng_from_geopoint(row: pd.Series, _) -> pd.Series:
    # GEO
    geopoint = row["_geopoint"].split(",")
    row["latitude"] = float(geopoint[0].strip())
    row["longitude"] = float(geopoint[1].strip())
    return row[["latitude", "longitude"]]


def _parse_float(value):
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


def compute_location(row: pd.Series, _):
    # first column is latitude, second is longitude
    lat_column = row.keys()[0]
    lng_column = row.keys()[1]
    row[lat_column] = _parse_float(row[lat_column])
    row[lng_column] = _parse_float(row[lng_column])
    row["location"] = get_point_from_location(row[lng_column], row[lat_column])
    return row[["location"]]


def get_point_from_location(longitude, latitude):
    if not longitude or not latitude or math.isnan(longitude) or math.isnan(latitude):
        return None
    return wkb.dumps(Point(longitude, latitude)).hex()


def clean_proposition_services(row, _):

    # formater les propositions de service selon les colonnes
    # action_codes and sous_categorie_codes
    #
    # [{'action': 'CODE_ACTION','sous_categories': ['CODE_SSCAT']}] ou []
    if row["sous_categorie_codes"]:
        row["proposition_service_codes"] = [
            {
                "action": action,
                "sous_categories": sorted(row["sous_categorie_codes"]),
            }
            for action in sorted(row["action_codes"])
        ]
    else:
        row["proposition_service_codes"] = []

    return row[["proposition_service_codes"]]


### Fonctions de résolution de l'adresse au format BAN et avec vérification via l'API
# adresse.data.gouv.fr en option
# TODO : A déplacer ?


def _get_address(
    adresse_format_ban: str,
) -> tuple[str, str, str]:
    if not adresse_format_ban:
        return ("", "", "")

    res = _get_address_from_ban(str(adresse_format_ban))
    match_percentage = res.get("match_percentage", 0)
    threshold = 80
    if match_percentage >= threshold:
        address = res.get("address")
        postal_code = res.get("postal_code")
        city = res.get("city")

        if not address or not postal_code or not city:
            address, postal_code, city = _extract_details(adresse_format_ban)
        return (address, postal_code, city)

    address, postal_code, city = _extract_details(adresse_format_ban)

    return (address, postal_code, city)


# TODO faire un retry avec tenacity
def _get_address_from_ban(address) -> dict:
    url = "https://api-adresse.data.gouv.fr/search/"
    params = {"q": address, "limit": 1}
    if address is None:
        return {}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if "features" in data and data["features"]:
            properties = data["features"][0]["properties"]
            label = properties.get("label")
            query = data["query"]
            address = properties.get("name")
            postal_code = properties.get("postcode")
            city = properties.get("city")
            match_percentage = fuzz.ratio(query.lower(), label.lower())
            coords = (
                data["features"][0].get("geometry", {}).get("coordinates", [None, None])
            )
            return {
                "latitude": coords[1],
                "longitude": coords[0],
                "query": query,
                "label": label,
                "address": address,
                "postal_code": postal_code,
                "city": city,
                "match_percentage": match_percentage,
            }
    return {}


def _address_details_clean_cedex(address_str: str) -> str:
    """Supprime les mentions CEDEX <NUM> de l'adresse."""
    cedex_pattern = re.compile(r"\bCEDEX\s*\d*\b", re.IGNORECASE)
    return cedex_pattern.sub("", address_str).strip()


def _address_details_extract(
    address_str: str,
) -> tuple[str, str, str]:
    """Extrait les détails de l'adresse, y compris le code postal et la ville."""
    address = postal_code = city = ""

    pattern1 = re.compile(
        rf"(.*)[{REGEX_BAN_SEPARATORS}]+(\d{{4,5}})[{REGEX_BAN_SEPARATORS}]*(.*)"
    )
    # Pattern pour capturer les codes postaux sans adresse
    pattern2 = re.compile(rf"(\d{{4,5}})[{REGEX_BAN_SEPARATORS}]*(.*)")
    if match := pattern1.search(address_str):
        address = match.group(1).strip(STRIP_BAN) if match.group(1) else ""
        postal_code = match.group(2).strip(STRIP_BAN) if match.group(2) else ""
        city = match.group(3).strip(STRIP_BAN) if match.group(3) else ""
    elif match := pattern2.search(address_str):
        postal_code = match.group(1).strip(STRIP_BAN) if match.group(1) else ""
        city = match.group(2).strip(STRIP_BAN) if match.group(2) else ""

    if city:
        city = city.title()
        city = city.replace("*", "").strip(STRIP_BAN)

    # Ajouter un zéro si le code postal a quatre chiffres
    postal_code = clean_code_postal(postal_code, None)

    return address, postal_code, city


def _extract_details(
    adresse_format_ban: str,
) -> tuple[str, str, str]:
    """Extrait les détails de l'adresse à partir d'une ligne de DataFrame."""
    if adresse_format_ban:
        address_str = _address_details_clean_cedex(adresse_format_ban)
        return _address_details_extract(address_str)
    return "", "", ""
