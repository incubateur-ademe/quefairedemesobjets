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
