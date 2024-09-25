from typing import List, cast
from django.core.cache import caches
import requests

db_cache = caches["database"]


def fetch_epci_codes() -> List[str]:
    response = requests.get("https://geo.api.gouv.fr/epcis/?fields=code")
    codes = [item["code"] for item in response.json()]
    return codes


def all_epci_codes_cached() -> List[str]:
    return cast(
        List[str],
        db_cache.get_or_set(
            "all_epci_codes", fetch_epci_codes, timeout=3600 * 24 * 365
        ),
    )


def retrieve_epci_bounding_box(epci):
    all_epcis_codes = db_cache.get_or_set(
        "all_epci_codes", fetch_epci_codes, timeout=3600 * 24 * 365
    )

    if epci not in all_epcis_codes:
        raise ValueError(f"The provided EPCI code does not seem to exist | {epci}")

    def fetch_epci_bounding_box():
        response = requests.get(
            f"https://geo.api.gouv.fr/epcis/{epci}?nom=Nan&fields=code,nom,contour"
        )
        contour = response.json()["contour"]
        return contour

    return db_cache.get_or_set(
        f"{epci}_bounding_box", fetch_epci_bounding_box, timeout=3600 * 24 * 365
    )
