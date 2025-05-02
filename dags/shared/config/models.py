import typing

from airflow.models.param import Param
from pydantic import BaseModel

PYDANTIC_TYPE_TO_AIRFLOW_TYPE = {
    bool: "boolean",
    str: "string",
    typing.Optional[str]: ["null", "string"],
    list[str]: "array",
    typing.Optional[list[str]]: ["null", "array"],
    list[int]: "array",
    typing.Optional[list[int]]: ["null", "array"],
}
EXTRA_ATTRIBUTES = [
    "examples",
    "description_md",
    "enum",
    "values_display",
]


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

        # Core attributes
        field_value = getattr(model_instance, field_name)  # Get value from instance
        assert field_info.annotation is not None
        param = {
            "default": field_value,
            "type": PYDANTIC_TYPE_TO_AIRFLOW_TYPE[field_info.annotation],
            "description_md": field_info.description,
        }

        # Extra attributes
        for extra_name in EXTRA_ATTRIBUTES:
            # Airflow params aligned with pydantic (e.g. "examples")
            if extra_value := getattr(field_info, extra_name, None):
                param[extra_name] = extra_value
            # Airflow params aligned NOT aligned with pydantic (e.g. "values_display")
            # have to be retrieved from json_schema_extra
            elif field_info.json_schema_extra and (
                extra_value := field_info.json_schema_extra.get(extra_name, None)
            ):
                param[extra_name] = extra_value

        # Instantiate and add to params
        params[field_name] = Param(**param)
    return params
