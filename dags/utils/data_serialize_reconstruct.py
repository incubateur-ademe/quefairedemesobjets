"""Functions to serialize and reconstruct the Django
data as we need to pass it over wire/JSON and thus have
to lose Python/Django objects"""

import logging
from datetime import datetime

from django.db import models

logger = logging.getLogger(__name__)


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
                else:
                    result[key] = value.pk
            elif key == "location":
                result["longitude"] = data["location"].x
                result["latitude"] = data["location"].y
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
    except Exception as e:
        logger.error(f"Error serializing for {model.__name__}, {data=}, {e=}")
        raise e

    return result
