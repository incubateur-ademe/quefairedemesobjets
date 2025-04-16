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

    try:
        if "longitude" in data and "latitude" in data:
            result["location"] = Point(data["longitude"], data["latitude"])
            # so we don't evaluate in below loop
            del data["longitude"]
            del data["latitude"]

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
                # If it's a foreign key, fetch the related entity
                related_instance = field.related_model.objects.get(pk=value)  # type: ignore
                result[key] = related_instance
            else:
                result[key] = value
    except Exception as e:
        logger.error(f"Error reconstructing for {model.__name__}, {data=}, {e=}")
        raise e
    return result
