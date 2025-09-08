import logging
import re
from typing import Any

import numpy as np
import pandas as pd
from opening_hours import OpeningHours, ParserError
from sources.config import shared_constants as constants
from sources.tasks.airflow_logic.config_management import DAGConfig
from sources.tasks.transform.formatter import format_libelle_to_code
from sources.tasks.transform.opening_hours import interprete_opening_hours

logger = logging.getLogger(__name__)

CLOSED_THIS_DAY = "Fermé"


def cast_eo_boolean_or_string_to_boolean(value: str | bool, _) -> bool | None:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, str):
        if value.lower().strip() in ["oui", "yes", "true"]:
            return True
        if value.lower().strip() in ["non", "no", "false"]:
            return False
    return None


def convert_opening_hours(opening_hours: str | None, _) -> str:
    opening_hours_by_day_of_week = interprete_opening_hours(opening_hours)
    displayed_opening_hours = []

    days = {
        "Mo": "lundi",
        "Tu": "mardi",
        "We": "mercredi",
        "Th": "jeudi",
        "Fr": "vendredi",
        "Sa": "samedi",
        "Su": "dimanche",
    }
    for day, hours in opening_hours_by_day_of_week.items():
        displayed_opening_hours_day = f"{days[day]}: "
        displayed_opening_hours_hours = []

        if hours:
            for hour in hours:
                displayed_opening_hours_hours.append(
                    f"{hour[0].strftime('%H:%M')} - {hour[1].strftime('%H:%M')}"
                )
            displayed_opening_hours_day += "; ".join(displayed_opening_hours_hours)
        else:
            displayed_opening_hours_day += CLOSED_THIS_DAY

        displayed_opening_hours.append(displayed_opening_hours_day)

    return "\n".join(displayed_opening_hours)


def clean_siren(siren: int | str | None) -> str:
    siren = clean_number(siren)

    if len(siren) == 9:
        return siren
    return ""


def clean_siret(siret: int | str | None) -> str:
    siret = clean_number(siret)

    if len(siret) == 9:
        return siret

    if len(siret) == 13:
        return "0" + siret

    if len(siret) == 14:
        return siret

    return ""


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
        return constants.PUBLIC_NP

    values_mapping = {
        "particuliers et professionnels": constants.PUBLIC_PRO_ET_PAR,
        "professionnels": constants.PUBLIC_PRO,
        "particuliers": constants.PUBLIC_PAR,
        "aucun": constants.PUBLIC_AUCUN,
        "dma/pro": constants.PUBLIC_PRO_ET_PAR,
        "dma": constants.PUBLIC_PAR,
        "pro": constants.PUBLIC_PRO,
        "np": constants.PUBLIC_NP,
    }

    return values_mapping.get(value.lower().strip(), constants.PUBLIC_NP)


def clean_reprise(value, _):
    if not value:
        return constants.REPRISE_NP

    values_mapping = {
        "1 pour 0": constants.REPRISE_1POUR0,
        "1 pour 1": constants.REPRISE_1POUR1,
        "non": constants.REPRISE_1POUR0,
        "oui": constants.REPRISE_1POUR1,
    }
    return values_mapping.get(value.lower().strip(), constants.REPRISE_NP)


def clean_url(url, _) -> str:
    if pd.isna(url) or not url:
        return ""
    url = str(url)

    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    return url


def clean_email(email: str | None, _) -> str:
    if pd.isna(email) or not email:
        return ""
    email = str(email).strip().lower()
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return ""
    return email


def clean_code_postal(cp: str | None, _) -> str:
    if pd.isna(cp) or not cp:
        return ""
    cp = clean_number(cp)
    return f"0{cp}" if cp and len(str(cp)) == 4 else str(cp)


def clean_horaires_osm(horaires_osm: str | None, _) -> str:
    if not horaires_osm:
        return ""
    # sometimes, hours are writen HHhMM instead of HH:MM
    # replace h using regex
    horaires_osm = re.sub(r"(\d{2})h(\d{2})", r"\1:\2", horaires_osm)
    try:
        OpeningHours(horaires_osm)
    except ParserError as e:
        logger.warning(f"Error parsing opening hours: {e}")
        return ""
    return horaires_osm


def clean_code_list(codes: str | None, _) -> list[str]:
    if codes is None:
        return []
    return [code.strip().lower() for code in codes.split("|") if code.strip().lower()]


def clean_sous_categorie_codes(
    sscat_list: str | list[str] | None, dag_config: DAGConfig
) -> list[str]:
    sous_categorie_codes = []

    if not sscat_list:
        return sous_categorie_codes

    if isinstance(sscat_list, str):
        sscat_list = sscat_list.split("|")
    if not isinstance(sscat_list, list):
        raise ValueError(
            f"Type {type(sscat_list)} not supported while cleaning sous_categorie_codes"
        )

    product_mapping = dag_config.product_mapping
    for sscat in sscat_list:
        sscat = sscat.strip().lower()
        if not sscat:
            continue
        sscat = product_mapping[sscat]
        if isinstance(sscat, str):
            sous_categorie_codes.append(sscat)
        elif isinstance(sscat, list):
            sous_categorie_codes.extend(sscat)
        else:
            raise ValueError(f"Type {type(sscat)} not supported in product_mapping")

    return list(set(sous_categorie_codes))


def clean_sous_categorie_codes_sinoe(
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

    return clean_sous_categorie_codes("|".join(sscat_list), dag_config)
