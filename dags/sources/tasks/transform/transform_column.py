import re
from typing import Any, Union

import pandas as pd


def mapping_try_or_fallback_column_value(
    df_column: pd.Series,
    values_mapping: dict,
    default_value: Union[str, bool, None] = None,
) -> pd.Series:
    # set to default value if column is not one of keys or values in values_mapping
    return (
        df_column.str.strip()
        .str.lower()
        .replace(values_mapping)
        .apply(lambda x: (default_value if x not in values_mapping.values() else x))
    )


def cast_eo_boolean_or_string_to_boolean(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower().strip() == "oui"
    return False


def convert_opening_hours(opening_hours: str | None) -> str:
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

    if not opening_hours or pd.isna(opening_hours):
        return ""

    return process_entry(opening_hours)


def clean_siren(siret: int | str | None) -> str:
    siret = clean_number(siret)

    if siret is None:
        return None

    if len(siret) == 9:
        return siret
    return ""


def clean_siret(siret: int | str | None) -> str:
    siret = clean_number(siret)

    if siret is None:
        return ""

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
