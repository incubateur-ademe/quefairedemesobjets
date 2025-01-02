import logging
import re

import pandas as pd
import requests
from fuzzywuzzy import fuzz
from sources.tasks.airflow_logic.config_management import DAGConfig
from sources.tasks.transform.transform_column import (
    clean_code_postal,
    clean_number,
    clean_siren,
    clean_siret,
)
from utils.formatter import format_libelle_to_code

logger = logging.getLogger(__name__)

ACTEUR_TYPE_DIGITAL = "acteur_digital"
ACTEUR_TYPE_ESS = "ess"
LABEL_ESS = "ess"
LABEL_TO_IGNORE = ["non applicable", "na", "n/a", "null", "aucun", "non"]


def merge_duplicates(
    df, group_column="identifiant_unique", merge_column="souscategorie_codes"
):

    df_duplicates = df[df.duplicated(group_column, keep=False)]
    df_non_duplicates = df[~df.duplicated(group_column, keep=False)]

    df_merged_duplicates = (
        df_duplicates.groupby(group_column)
        .agg(
            {
                **{
                    col: "first"
                    for col in df.columns
                    if col != merge_column and col != group_column
                },
                merge_column: _merge_columns_of_accepted_products,
            }
        )
        .reset_index()
    )

    # Concatenate the non-duplicates and merged duplicates
    df_final = pd.concat([df_non_duplicates, df_merged_duplicates], ignore_index=True)

    return df_final


def _merge_columns_of_accepted_products(group):
    produits_sets = set()
    for produits in group:
        produits_sets.update(produits)
    return sorted(produits_sets)


def clean_telephone(row: pd.Series, _):
    telephone_column = list(row.keys())[0]
    number = clean_number(row[telephone_column])

    if number is None:
        row[["telephone"]] = None
        return row[["telephone"]]

    if len(number) == 9 and row["code_postal"] and int(row["code_postal"]) < 96000:
        number = "0" + number

    if number.startswith("33"):
        number = "0" + number[2:]

    if len(number) < 6:
        number = None

    row["telephone"] = number
    return row[["telephone"]]


# TODO : Ajouter des tests
def clean_siret_and_siren(row, _):
    if "siret" in row:
        row["siret"] = clean_siret(row["siret"])
    else:
        row["siret"] = None
    if "siren" in row and row["siren"]:
        row["siren"] = clean_siren(row["siren"])
    else:
        row["siren"] = (
            row["siret"][:9] if "siret" in row and row["siret"] is not None else None
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
    return row[["identifiant_externe"]]


def clean_identifiant_unique(row, _):
    if not row.get("identifiant_externe"):
        raise ValueError(
            "identifiant_externe is required to generate identifiant_unique"
        )
    unique_str = row["identifiant_externe"].replace("/", "-").strip()
    if row.get("acteur_type_code") == ACTEUR_TYPE_DIGITAL:
        unique_str = unique_str + "_d"
    row["identifiant_unique"] = row.get("source_code").lower() + "_" + unique_str
    return row[["identifiant_unique"]]


def merge_sous_categories_columns(row, _):
    categories = [row[col] for col in row.keys() if pd.notna(row[col]) and row[col]]
    row["produitsdechets_acceptes"] = " | ".join(categories)
    return row[["produitsdechets_acceptes"]]


def clean_adresse(row, dag_config):
    row["adresse"] = row["adresse_format_ban"]
    address = postal_code = city = None
    if dag_config.validate_address_with_ban:
        address, postal_code, city = _get_address(row["adresse_format_ban"])
    else:
        address, postal_code, city = _extract_details(row["adresse_format_ban"])
    row["adresse"] = address
    row["code_postal"] = postal_code
    row["ville"] = city
    return row[["adresse", "code_postal", "ville"]]


def clean_acteurservice_codes(row, _):
    acteurservice_codes = []
    if row.get("point_dapport_de_service_reparation") or row.get("point_de_reparation"):
        acteurservice_codes.append("service_de_reparation")
    if row.get("point_dapport_pour_reemploi") or row.get(
        "point_de_collecte_ou_de_reprise_des_dechets"
    ):
        acteurservice_codes.append("structure_de_collecte")
    row["acteurservice_codes"] = acteurservice_codes
    return row[["acteurservice_codes"]]


def clean_action_codes(row, _):
    action_codes = []
    if row.get("point_dapport_de_service_reparation") or row.get("point_de_reparation"):
        action_codes.append("reparer")
    if row.get("point_dapport_pour_reemploi"):
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


def merge_and_clean_souscategorie_codes(
    row: pd.Series, dag_config: DAGConfig
) -> pd.Series:
    categories = [row[col] for col in row.keys() if pd.notna(row[col]) and row[col]]
    souscategorie_codes = []
    product_mapping = dag_config.product_mapping
    for sscat in categories:
        sscat = sscat.strip().lower()
        sscat = product_mapping[sscat]
        if isinstance(sscat, str):
            souscategorie_codes.append(sscat)
        elif isinstance(sscat, list):
            souscategorie_codes.extend(sscat)
        else:
            raise ValueError(
                f"Type {type(sscat)} not supported for souscategorie_codes"
            )
    row["souscategorie_codes"] = list(set(souscategorie_codes))
    return row[["souscategorie_codes"]]


def get_latlng_from_geopoint(row: pd.Series, _) -> pd.Series:
    # GEO
    geopoint = row["_geopoint"].split(",")
    row["latitude"] = float(geopoint[0].strip())
    row["longitude"] = float(geopoint[1].strip())
    return row[["latitude", "longitude"]]


### Fonctions de résolution de l'adresse au format BAN et avec vérification via l'API
# adresse.data.gouv.fr en option
# TODO : A déplacer ?


def _get_address(
    adresse_format_ban: str,
) -> tuple[str | None, str | None, str | None]:
    if not adresse_format_ban:
        return (None, None, None)

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
) -> tuple[str | None, str | None, str | None]:
    """Extrait les détails de l'adresse, y compris le code postal et la ville."""
    address = postal_code = city = None

    # Pattern pour capturer les codes postaux et les noms de ville optionnels
    pattern1 = re.compile(r"(.*)\s+(\d{4,5})\s*(.*)")
    # Pattern pour capturer les codes postaux sans adresse
    pattern2 = re.compile(r"(\d{4,5})\s*(.*)")
    if match := pattern1.search(address_str):
        address = match.group(1).strip() if match.group(1) else None
        postal_code = match.group(2).strip() if match.group(2) else None
        city = match.group(3).strip() if match.group(3) else None
    elif match := pattern2.search(address_str):
        postal_code = match.group(1).strip() if match.group(1) else None
        city = match.group(2).strip() if match.group(2) else None

    if city:
        city = city.title()
        city = city.replace("*", "").strip()

    # Ajouter un zéro si le code postal a quatre chiffres
    postal_code = clean_code_postal(postal_code, None)

    return address, postal_code, city


def _extract_details(
    adresse_format_ban: str,
) -> tuple[str | None, str | None, str | None]:
    """Extrait les détails de l'adresse à partir d'une ligne de DataFrame."""
    if adresse_format_ban:
        address_str = _address_details_clean_cedex(adresse_format_ban)
        return _address_details_extract(address_str)
    return None, None, None
