import typing

from airflow.models.param import Param
from pydantic import BaseModel

PYDANTIC_TYPE_TO_AIRFLOW_TYPE = {
    bool: "boolean",
    str: "string",
    typing.Optional[str]: ["null", "string"],
    list[str]: ["array"],
}


def config_to_airflow_params(model_instance: BaseModel) -> dict[str, Param]:
    """Generate Airflow params from a pydantic config model instance:

    TODO: to implement recurring/complex types, we can use a mapping
    with field_name as entry, and keep the generic fallback below

    if field_name == "complex_field":
        params = PARAMS[field_name]
    elif:
        ...
    else:
        fallback to current logic
    """
    params = {}
    model_cls = model_instance.__class__
    for field_name, field_info in model_cls.model_fields.items():
        field_value = getattr(model_instance, field_name)  # Get value from instance

        params[field_name] = Param(
            field_value,
            type=PYDANTIC_TYPE_TO_AIRFLOW_TYPE[field_info.annotation],
            description_md=field_info.description,
        )
    return params
