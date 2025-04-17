# TODO: to be centralised as we have this logic
# scattered here and in various places in dags/
import logging

from django.contrib.gis.geos import Point
from django.db import models

logger = logging.getLogger(__name__)


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


def data_reconstruct(model: type[models.Model], data_src: dict) -> dict:
    """
    Reconstruct data ready to use in Django model.

    Args:
    - model_class: The Django model class.
    - data: The dictionary containing the data to reconstruct.

    Returns:
    - An instance of the model with the data populated.
    """
    result = {}
    data = data_src.copy()

    if "longitude" in data and "latitude" in data:
        result["location"] = Point(data.pop("longitude"), data.pop("latitude"))

    for key, value in data.items():
        field = model._meta.get_field(key)

        # We don't try to be fancy with None, it's None
        if value is None:
            # Same explanation as in data_serialize
            if key == "location":
                continue
            else:
                result[key] = value
        elif isinstance(field, models.ForeignKey):
            # Normalizing to {field} from {field}_id so all fields are
            # represented in their Django flavour
            if key.endswith("_id"):
                try:
                    key_no_id = key.rstrip("_id")
                    field = model._meta.get_field(key_no_id)
                    key = key_no_id
                except Exception:
                    pass

            # Retrieving the related instance if it's not already an instance
            if not isinstance(value, field.related_model):  # type: ignore
                value = field.related_model.objects.get(pk=value)  # type: ignore

            result[key] = value

        else:
            result[key] = value

    return result
