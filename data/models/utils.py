from django.contrib.gis.geos import Point


def data_latlong_to_location(data: dict) -> dict:
    """Convert latitude and longitude to location from a dictionary"""
    result = data.copy()
    if "latitude" in result and "longitude" in result:
        result["location"] = Point(
            float(result["longitude"]), float(result["latitude"])
        )
        del result["latitude"]
        del result["longitude"]
    return result
