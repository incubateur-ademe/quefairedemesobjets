# TODO: to be centralised as we have this logic
# scattered here and in various places in dags/
from django.contrib.gis.geos import Point


def parent_data_prepare(data: dict) -> dict:
    """Make some parent data compatible with the
    acteur model"""

    # We can't handle location over JSON when passed from
    # the clustering DAG, we have to split into long/lat
    # and reconstruct
    if "longitude" in data and "latitude" in data:
        data["location"] = Point(data["longitude"], data["latitude"])
        del data["longitude"]
        del data["latitude"]
    return data
