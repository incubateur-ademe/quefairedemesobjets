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


class OCAConfig(BaseModel):
    prefix: str | None = None
    deduplication_source: bool = False


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
    metadata_endpoint: str | None = None
    label_bonus_reparation: Optional[str] = None
    product_mapping: dict
    source_code: Optional[str] = None
    validate_address_with_ban: bool = False
    oca: OCAConfig | None = None
    returnable_objects: bool = False

    @field_validator("endpoint")
    def validate_endpoint(cls, endpoint):
        if endpoint.startswith("s3://"):
            if not endpoint.endswith(".xlsx"):
                raise ValueError("S3 URL must end with '.xlsx'")

            if not re.match(r"^s3://[a-zA-Z0-9.\-_]+(/[a-zA-Z0-9.\-_]+)*$", endpoint):
                raise ValueError("Invalid S3 URL format")

        elif endpoint.startswith("https://") or endpoint.startswith("http://"):
            if not re.match(r"^https?://[^/\s]+[^\s]*$", endpoint):
                raise ValueError("Invalid HTTP URL format")

        else:
            raise ValueError("URL must start with 's3://' or 'http(s)://'")

        return endpoint

    @field_validator("metadata_endpoint")
    def validate_metadata_endpoint(cls, metadata_endpoint):
        if metadata_endpoint is not None:
            if not re.match(r"^https?://[^/\s]+[^\s]*$", metadata_endpoint):
                raise ValueError(
                    "if metadata_endpoint is set, it must be a valid HTTP URL"
                )
        return metadata_endpoint

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

    @property
    def oca_deduplication_source(self) -> bool:
        if self.oca is None:
            return False
        return bool(self.oca.deduplication_source)

    @property
    def is_oca(self) -> bool:
        return bool(self.oca)

    @property
    def oca_prefix(self) -> str | None:
        if self.oca is None:
            return None
        return self.oca.prefix


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
