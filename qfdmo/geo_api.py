from typing import List, Tuple, cast

import requests
from django.contrib.gis.geos import GEOSGeometry
from django.core.cache import caches

db_cache = caches["database"]


def fetch_epci_codes() -> List[Tuple[str, str]]:
    """Retrieves EPCI codes from geo.api"""
    response = requests.get("https://geo.api.gouv.fr/epcis/?fields=code,nom")
    codes = [(item["code"], item["nom"]) for item in response.json()]
    return codes


def all_epci_codes():
    return cast(
        List[Tuple[str, str]],
        db_cache.get_or_set(
            "all_epci_codes", fetch_epci_codes, timeout=3600 * 24 * 365
        ),
    )


def retrieve_epci_geojson(epci):
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


def bbox_from_list_of_geojson(geojson_list, buffer: float = 0):
    """Returns a bbox from a list of geojson

    The buffer can be used if you want to extend the size of the bounding box.
    Examples :
    - For an EPCI, a value of 0.2 is fine
    """
    geometries = [GEOSGeometry(str(geojson)) for geojson in geojson_list]
    geometry_union = geometries.pop(0)
    for geometry in geometries:
        geometry_union = geometry_union.union(geometry)

    bigger_geom = geometry_union.buffer(buffer)
    return bigger_geom.extent
