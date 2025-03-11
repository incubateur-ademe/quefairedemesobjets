import json
import re
from typing import Optional, Union

# types.py
from pydantic import BaseModel, field_validator


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
    value: Union[str, bool, list[str]]


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
    normalization_rules: list[
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
    s3_connection_id: str | None = None
    endpoint: str  # HttpURL or s3URL
    label_bonus_reparation: Optional[str] = None
    product_mapping: dict
    source_code: Optional[str] = None
    validate_address_with_ban: bool = False

    @field_validator("endpoint")
    def validate_endpoint(cls, v):
        if v.startswith("s3://"):
            # We only accept xlsx files from s3
            if not v.endswith(".xlsx"):
                raise ValueError("L'URL S3 doit se terminer par '.xlsx'")

            # Check if the endpoint is a valid s3 file url
            s3_pattern = r"^s3://[a-zA-Z0-9.\-_]+(/[a-zA-Z0-9.\-_]+)*$"
            if not re.match(s3_pattern, v):
                raise ValueError("Format d'URL S3 invalide")

        elif v.startswith("https://") or v.startswith("http://"):
            # check if the endpoint is a valid http url
            if not re.match(r"^https?://[^/\s]+[^\s]*$", v):
                raise ValueError("Format d'URL HTTP invalide")

        else:
            raise ValueError("L'URL doit commencer par 's3://' ou 'http(s)://'")

        return v

    @classmethod
    def from_airflow_params(
        cls, params: dict[str, Union[str, list, dict]]
    ) -> "DAGConfig":

        params["normalization_rules"] = get_nested_config_parameter(
            params.get("normalization_rules", [])
        )
        return cls.model_validate(params)

    def get_expected_columns(self) -> set[str]:
        columns = set()
        for transformation in self.normalization_rules:
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
        removed_columns = [
            transformation.remove
            for transformation in self.normalization_rules
            if isinstance(transformation, NormalizationColumnRemove)
        ]
        columns -= set(removed_columns)
        return columns


# DEPRECATED
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
