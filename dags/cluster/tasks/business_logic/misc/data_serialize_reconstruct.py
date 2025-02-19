"""Functions to serialize and reconstruct the Django
data as we need to pass it over wire/JSON and thus have
to lose Python/Django objects"""

from datetime import datetime

from django.contrib.gis.geos import Point
from django.db import models


def data_serialize(model: type[models.Model], data: dict) -> dict:
    """
    Serialize a dictionary to match the Django model structure.

    Args:
    - model_class: The Django model class.
    - data: The dictionary containing the data to serialize.

    Returns:
    - A dictionary with values adjusted to match the model's requirements.
    """
    result = {}

    for key, value in data.items():
        field = model._meta.get_field(key)

        if isinstance(field, models.ForeignKey):
            if isinstance(value, (str, int)):
                result[key] = value
            else:
                result[key] = value.pk
        elif key == "location":
            result["longitude"] = data["location"].x
            result["latitude"] = data["location"].y
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        else:
            result[key] = value

    return result


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
        result["location"] = Point(data["longitude"], data["latitude"])
        # so we don't evaluate in below loop
        del data["longitude"]
        del data["latitude"]

    for key, value in data.items():
        field = model._meta.get_field(key)

        if isinstance(field, models.ForeignKey):
            # If it's a foreign key, fetch the related entity
            related_instance = field.related_model.objects.get(pk=value)  # type: ignore
            result[key] = related_instance
        else:
            result[key] = value

    return result
