import json
from typing import Optional, Union

# types.py
from pydantic import BaseModel, HttpUrl


# Renommage des colonnes
# Format : { "origin": "col origin", "destination": "col origin" }
class NormalizationColumnRename(BaseModel):
    origin: str
    destination: str


# Transformation des colonnes
class NormalizationColumnTransform(BaseModel):
    origin: str
    destination: str
    transformation: str


# Ajout des colonnes avec une valeur par défaut
class NormalizationColumnDefault(BaseModel):
    column: str
    value: str


# Transformation du dataframe
class NormalizationDFTransform(BaseModel):
    origin: list[str]
    destination: list[str]
    transformation: str


# Supression des colonnes
class NormalizationColumnRemove(BaseModel):
    remove: str


# Colonnes à garder (rien à faire, utilisé pour le controle)
class NormalizationColumnKeep(BaseModel):
    keep: str


class DAGConfig(BaseModel):
    column_transformations: list[
        Union[
            NormalizationColumnRename,
            NormalizationColumnTransform,
            NormalizationColumnDefault,
            NormalizationDFTransform,
            NormalizationColumnRemove,
            NormalizationColumnKeep,
        ]
    ]
    combine_columns_categories: list[str] = []
    dechet_mapping: dict = {}
    endpoint: HttpUrl
    ignore_duplicates: bool = False
    label_bonus_reparation: Optional[str] = None
    merge_duplicated_acteurs: bool = False
    product_mapping: dict
    source_code: Optional[str] = None
    validate_address_with_ban: bool = False
    validate_address_with_ban: bool = False

    @classmethod
    def from_airflow_params(
        cls, params: dict[str, Union[str, list, dict]]
    ) -> "DAGConfig":

        def _get_nested_config_parameter(
            config_parameter: list | dict | str,
        ) -> list | dict | str:
            """
            We need this function because Airflow does not support nested parameters
            in case of list of dict, the dict is converted to string and we need to
            convert it back to dict we do it recursively to handle any case of nested
            parameters
            """
            if isinstance(config_parameter, str):
                try:
                    value = json.loads(config_parameter.replace("'", '"'))
                    return get_nested_config_parameter(value)
                except json.JSONDecodeError:
                    return config_parameter
            if isinstance(config_parameter, list):
                return [
                    get_nested_config_parameter(value) for value in config_parameter
                ]
            if isinstance(config_parameter, dict):
                return {
                    key: get_nested_config_parameter(value)
                    for key, value in config_parameter.items()
                }

            raise ValueError(
                "config_parameter must be a list, dict or string,"
                f" not : {type(config_parameter)}"
            )

        params["column_transformations"] = _get_nested_config_parameter(
            params.get("column_transformations", [])
        )
        return cls.model_validate(params)

    def get_expected_columns(self) -> set[str]:
        columns = set()
        for transformation in self.column_transformations:
            if isinstance(transformation, NormalizationColumnRename):
                columns.add(transformation.destination)
            elif isinstance(transformation, NormalizationColumnTransform):
                columns.add(transformation.destination)
            elif isinstance(transformation, NormalizationDFTransform):
                columns.update(transformation.destination)
            elif isinstance(transformation, NormalizationColumnDefault):
                columns.add(transformation.column)
            elif isinstance(transformation, NormalizationColumnKeep):
                columns.add(transformation.keep)
        return columns


def get_nested_config_parameter(
    config_parameter: list | dict | str,
) -> list | dict | str:
    """
    We need this function because Airflow does not support nested parameters in case of
    list of dict, the dict is converted to string and we need to convert it back to dict
    we do it recursively to handle any case of nested parameters
    """
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
