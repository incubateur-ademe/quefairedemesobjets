"""Functions to serialize and reconstruct the Django
data as we need to pass it over wire/JSON and thus have
to lose Python/Django objects"""

import logging
from datetime import datetime
from typing import Any

from utils.django import django_setup_full

logger = logging.getLogger(__name__)


def value_to_json_ready(key: str, value):
    """Convert a parent_data_new value to a JSON-serializable form."""

    django_setup_full()
    from django.db import models
    from qfdmo.models.utils import django_model_to_wire

    if value is None:
        return None
    if key == "location" and hasattr(value, "x") and hasattr(value, "y"):
        return [value.x, value.y]
    if isinstance(value, models.Model):
        return django_model_to_wire(value)
    return value


def parent_data_dict_to_json_ready(data: dict | None) -> dict | None:
    if data is None or not isinstance(data, dict):
        return data
    return {key: value_to_json_ready(key, value) for key, value in data.items()}


def location_to_coords(location) -> tuple:
    """Extract (longitude, latitude) from common location representations."""
    if hasattr(location, "x") and hasattr(location, "y"):
        return location.x, location.y
    if isinstance(location, (list, tuple)):
        return location[0], location[1]
    if isinstance(location, str):
        from django.contrib.gis.geos import GEOSGeometry

        point = GEOSGeometry(location)
        return point.x, point.y
    raise TypeError(f"Unsupported location type: {type(location)}")


def data_serialize(model: type[Any], data: dict) -> dict:
    """
    Serialize a dictionary to match the Django model structure.

    Args:
    - model_class: The Django model class.
    - data: The dictionary containing the data to serialize.

    Returns:
    - A dictionary with values adjusted to match the model's requirements.
    """
    django_setup_full()
    from django.db import models
    from qfdmo.models.utils import django_model_to_wire

    result = {}

    try:
        for key, value in data.items():
            field = model._meta.get_field(key)

            # We don't try to be fancy with None, it's None
            if value is None:
                # Due to clean_location check on Acteur model
                # which prevents None if acteur is non-digital
                # AND the fact that we can't know for sure whether
                # acteur is digital or not, we just skip None locations
                # TODO: we need to revamp the validation architecture
                # as those if-elses all over the code are not maintainable
                if key == "location":
                    continue
                else:
                    result[key] = value
            elif isinstance(field, models.ForeignKey):
                if isinstance(value, (str, int)):
                    result[key] = value
                elif isinstance(value, float):
                    result[key] = int(value)
                elif isinstance(value, models.Model):
                    result[key] = django_model_to_wire(value)
                else:
                    logger.info(f"Serializing foreign key {key} with value {value}")
                    result[key] = value.pk
            elif key == "location":
                longitude, latitude = location_to_coords(value)
                result["longitude"] = longitude
                result["latitude"] = latitude
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
    except Exception as e:
        logger.error(f"Error serializing for {model.__name__}, {data=}, {e=}")
        raise e

    return result
