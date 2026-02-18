from django.contrib.gis.geos import Point


def prepare_acteur_data_with_location(acteur_data: dict) -> dict:
    """Convert latitude and longitude to location from a dictionary"""
    result = acteur_data.copy()
    result = {
        k: v
        for k, v in result.items()
        if not k.endswith("_code") and not k.endswith("_codes")
    }
    if "latitude" in result and "longitude" in result:
        if result["latitude"] is not None and result["longitude"] is not None:
            result["location"] = Point(
                float(result["longitude"]), float(result["latitude"])
            )
        del result["latitude"]
        del result["longitude"]
    return result
