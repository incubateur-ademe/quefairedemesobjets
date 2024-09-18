from typing import TypedDict, List, cast
from django.core.cache import caches
import json
import requests

db_cache = caches["database"]


def fetch_epci_codes() -> List[str]:
    response = requests.get("https://geo.api.gouv.fr/epcis/?fields=code")
    codes = [item["code"] for item in response.json()]
    return codes


def all_epci_codes() -> List[str]:
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


class PointDict(TypedDict):
    lat: float
    lng: float


class LeafletBbox(TypedDict):
    center: List[str]
    southWest: PointDict
    northEast: PointDict


def sanitize_leaflet_bbox(custom_bbox_as_string: str) -> List[float] | None:
    custom_bbox: LeafletBbox = json.loads(custom_bbox_as_string)

    try:
        return [
            custom_bbox["southWest"]["lng"],
            custom_bbox["southWest"]["lat"],
            custom_bbox["northEast"]["lng"],
            custom_bbox["northEast"]["lat"],
        ]
    except (KeyError, TypeError) as exception:
        # TODO : gérer l'erreur
        print(f"Uh oh {exception=}")
        return []
