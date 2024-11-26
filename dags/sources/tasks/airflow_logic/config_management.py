import json


def get_nested_config_parameter(
    config_parameter: list | dict | str,
) -> list | dict | str:
    if isinstance(config_parameter, str):
        try:
            value = json.loads(config_parameter.replace("'", '"'))
            return get_nested_config_parameter(value)
        except json.JSONDecodeError:
            return config_parameter
    if isinstance(config_parameter, list):
        return [get_nested_config_parameter(value) for value in config_parameter]
    if isinstance(config_parameter, dict):
        return {
            key: get_nested_config_parameter(value)
            for key, value in config_parameter.items()
        }

    raise ValueError(
        "config_parameter must be a list, dict or string,"
        f" not : {type(config_parameter)}"
    )
