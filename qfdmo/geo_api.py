import itertools
import logging
from typing import List, Tuple, Union, cast

import requests
from django.contrib.gis.geos import GEOSGeometry
from django.core.cache import caches
from rapidfuzz import fuzz, process

db_cache = caches["database"]


logger = logging.getLogger(__name__)

BASE_URL = "https://geo.api.gouv.fr"


def formatted_epcis_list() -> List[str]:
    formatted = [f"{nom} - {code}" for nom, code in epcis_from(["nom", "code"])]
    return formatted


def formatted_epcis_as_list_of_tuple() -> List[Tuple[str, str]]:
    return [(item, item) for item in formatted_epcis_list()]


def search_epci_code(query) -> List[str]:
    results = process.extract(
        query.lower(),
        formatted_epcis_list(),
        scorer=fuzz.WRatio,
        limit=5,
    )
    return [match for match, score, index in results]


def fetch_epci_codes() -> List[str]:
    """Retrieves EPCI codes from geo.api"""
    response = requests.get(f"{BASE_URL}/epcis/?fields=code,nom")
    return response.json()


def epcis_from(fields: List[str] = []) -> Union[List, List[tuple]]:
    """Retrieves a list of fields from the geo.api
    At the moment only nom and code fields are supported.
    The fields are returned in the same order they are passed in the parameter
    """
    raw_codes = cast(
        List,
        db_cache.get_or_set("all_epci_codes", fetch_epci_codes, timeout=3600 * 24 * 30),
    )
    epcis = [[code.get(field) for field in fields] for code in raw_codes]

    # This can be handy if we just need a list of codes and not
    # a list of list of codes.
    if len(fields) == 1:
        return list(itertools.chain.from_iterable(epcis))

    return epcis


def retrieve_epci_geojson(epci):
    all_codes = epcis_from(["code"])
    if epci not in all_codes:
        raise ValueError(f"The provided EPCI code does not seem to exist | {epci}")

    def fetch_epci_bounding_box():
        response = requests.get(
            f"{BASE_URL}/epcis/{epci}?nom=Nan&fields=code,nom,contour"
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
