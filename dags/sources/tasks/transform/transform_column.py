import logging
import re
from typing import Any

import pandas as pd
from sources.config import shared_constants as constants
from sources.tasks.airflow_logic.config_management import DAGConfig
from utils.formatter import format_libelle_to_code

logger = logging.getLogger(__name__)


def cast_eo_boolean_or_string_to_boolean(value: str | bool, _) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower().strip() == "oui"
    return False


def convert_opening_hours(opening_hours: str | None, _) -> str:
    french_days = {
        "Mo": "lundi",
        "Tu": "mardi",
        "We": "mercredi",
        "Th": "jeudi",
        "Fr": "vendredi",
        "Sa": "samedi",
        "Su": "dimanche",
    }

    def translate_hour(hour):
        return hour.replace(":", "h").zfill(5)

    def process_schedule(schedule):
        parts = schedule.split(",")
        translated = []
        for part in parts:
            start, end = part.split("-")
            translated.append(f"de {translate_hour(start)} à {translate_hour(end)}")
        return " et ".join(translated)

    def process_entry(entry):
        days, hours = entry.split(" ")
        day_range = " au ".join(french_days[day] for day in days.split("-"))
        hours_translated = process_schedule(hours)
        return f"du {day_range} {hours_translated}"

    if pd.isna(opening_hours) or not opening_hours:
        return ""

    return process_entry(opening_hours)


def clean_siren(siren: int | str | None) -> str | None:
    siren = clean_number(siren)

    if len(siren) == 9:
        return siren
    return None


def clean_siret(siret: int | str | None) -> str | None:
    siret = clean_number(siret)

    if len(siret) == 9:
        return siret

    if len(siret) == 13:
        return "0" + siret

    if len(siret) == 14:
        return siret

    return None


def clean_number(number: Any) -> str:
    if pd.isna(number) or number is None:
        return ""

    # suppression des 2 derniers chiffres si le caractère si == .0
    number = re.sub(r"\.0$", "", str(number))
    # suppression de tous les caractères autre que digital
    number = re.sub(r"[^\d+]", "", number)
    return number


def strip_string(value: str | None, _) -> str:
    return str(value).strip() if not pd.isna(value) and value else ""


def strip_lower_string(value: str | None, _) -> str:
    return str(value).strip().lower() if not pd.isna(value) and value else ""


def clean_acteur_type_code(value, _):
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
        "point d'apport volontaire prive": "pav_prive",
        "plateforme inertes": "plateforme_inertes",
        "magasin / franchise, enseigne commerciale / distributeur / point de vente "
        "/ franchise, enseigne commerciale / distributeur / point de vente": "commerce",
        "point d'apport volontaire ephemere / ponctuel": "pav_ponctuel",
    }
    code = mapping_dict.get(format_libelle_to_code(value), None)
    if code is None:
        raise ValueError(f"Acteur type `{value}` not found in mapping")
    return code


def clean_public_accueilli(value, _):
    if not value:
        return None

    values_mapping = {
        "particuliers et professionnels": constants.PUBLIC_PRO_ET_PAR,
        "professionnels": constants.PUBLIC_PRO,
        "particuliers": constants.PUBLIC_PAR,
        "aucun": constants.PUBLIC_AUCUN,
        "dma/pro": constants.PUBLIC_PRO_ET_PAR,
        "dma": constants.PUBLIC_PAR,
        "pro": constants.PUBLIC_PRO,
        "np": None,
    }

    return values_mapping.get(value.lower().strip())


def clean_reprise(value, _):
    if not value:
        return None

    values_mapping = {
        "1 pour 0": constants.REPRISE_1POUR0,
        "1 pour 1": constants.REPRISE_1POUR1,
        "non": constants.REPRISE_1POUR0,
        "oui": constants.REPRISE_1POUR1,
    }
    return values_mapping.get(value.lower().strip())


def clean_url(url, _) -> str:
    if pd.isna(url) or not url:
        return ""
    url = str(url)

    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    return url


def clean_code_postal(cp: str | None, _) -> str:
    if pd.isna(cp) or not cp:
        return ""
    # cast en str et ajout de 0 si le code postal est inférieur à 10000
    return f"0{cp}" if cp and len(str(cp)) == 4 else str(cp)


def clean_souscategorie_codes(
    sscat_list: str | None, dag_config: DAGConfig
) -> list[str]:
    souscategorie_codes = []

    if not sscat_list:
        return souscategorie_codes

    product_mapping = dag_config.product_mapping
    for sscat in sscat_list.split("|"):
        sscat = sscat.strip().lower()
        if not sscat:
            continue
        sscat = product_mapping[sscat]
        if isinstance(sscat, str):
            souscategorie_codes.append(sscat)
        elif isinstance(sscat, list):
            souscategorie_codes.extend(sscat)
        else:
            raise ValueError(f"Type {type(sscat)} not supported in product_mapping")

    return list(set(souscategorie_codes))


def clean_souscategorie_codes_sinoe(
    sscats: str | None, dag_config: DAGConfig
) -> list[str]:

    if not sscats:
        return []

    dechet_mapping = dag_config.dechet_mapping
    product_mapping = dag_config.product_mapping

    # on cinde les codes déchêts en liste (ex: "01.3|02.31" -> ["01.3", "02.31"])
    sscat_list = sscats.split("|")

    # nettoyage après cindage
    sscat_list = [
        v.strip()
        for v in sscat_list
        if v.strip().lower() not in ("", "nan", "np", "none")
    ]
    sscat_list = [
        dechet_mapping[v]
        for v in sscat_list
        if dechet_mapping[v].lower() in product_mapping
    ]

    return clean_souscategorie_codes("|".join(sscat_list), dag_config)
