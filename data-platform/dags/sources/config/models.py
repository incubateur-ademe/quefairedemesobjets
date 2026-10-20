import json
import re
import types
from typing import Any, Optional, Union, get_args, get_origin

from airflow.sdk import Param
from pydantic import BaseModel, Field, field_validator
from shared.config.models import EXTRA_ATTRIBUTES, PYDANTIC_TYPE_TO_AIRFLOW_TYPE


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


NormalizationRules = list[
    Union[
        NormalizationColumnRename,
        NormalizationColumnTransform,
        NormalizationColumnDefault,
        NormalizationDFTransform,
        NormalizationColumnRemove,
        NormalizationColumnKeep,
    ]
]

# Champ non exposé dans les paramètres Airflow : une sous-classe doit le redéclarer
# pour l'exposer.
HIDDEN_FROM_AIRFLOW = {"airflow_param": False}


class SourceConfig(BaseModel):
    """Configuration d'un DAG source.

    Les tâches lisent cette classe ; chaque DAG instancie la sous-classe adaptée à sa
    source, qui détermine les paramètres affichés dans Airflow.
    """

    normalization_rules: NormalizationRules
    endpoint: str = Field(description="URL HTTP(S) ou S3 du jeu de données source.")
    metadata_endpoint: str | None = Field(
        default=None,
        description="URL du schéma metadata (pointsapport / data-fair).",
    )
    validate_address_with_ban: bool = Field(
        default=False,
        description="Valider les adresses via l'API BAN lorsque la source le permet.",
    )
    product_mapping: dict = Field(
        description="Mapping produits / sous-catégories utilisé à la normalisation."
    )
    use_legacy_suggestions: bool = Field(
        default=False,
        description="Utiliser l'ancien pipeline de suggestions type/action.",
    )
    save_datasource_in_warehouse_db: bool = Field(
        default=True,
        description=(
            "Enregistrer les données téléchargées dans l'entrepôt "
            "(vue `{dag_id}_in_use`) au lieu de les transmettre via XCom entre "
            "download et normalize."
        ),
    )

    combine_columns_categories: list[str] = Field(
        default_factory=list, json_schema_extra=HIDDEN_FROM_AIRFLOW
    )
    dechet_mapping: dict = Field(
        default_factory=dict, json_schema_extra=HIDDEN_FROM_AIRFLOW
    )
    s3_connection_id: str | None = Field(
        default=None, json_schema_extra=HIDDEN_FROM_AIRFLOW
    )
    label_bonus_reparation: Optional[str] = Field(
        default=None, json_schema_extra=HIDDEN_FROM_AIRFLOW
    )
    source_code: Optional[str] = Field(
        default=None, json_schema_extra=HIDDEN_FROM_AIRFLOW
    )
    oca: OCAConfig | None = Field(default=None, json_schema_extra=HIDDEN_FROM_AIRFLOW)
    returnable_objects: bool = Field(
        default=False, json_schema_extra=HIDDEN_FROM_AIRFLOW
    )
    ignore_rows_with_null_or_empty_fields: list[str] = Field(
        default_factory=list, json_schema_extra=HIDDEN_FROM_AIRFLOW
    )

    @field_validator("endpoint")
    @classmethod
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
    @classmethod
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
    ) -> "SourceConfig":

        params["normalization_rules"] = get_nested_config_parameter(
            params.get("normalization_rules", [])
        )
        return cls.model_validate(params)

    def to_airflow_params(self) -> dict[str, Param]:
        params: dict[str, Param] = {}
        for field_name, field_info in type(self).model_fields.items():
            if field_info.json_schema_extra == HIDDEN_FROM_AIRFLOW:
                continue
            field_value = getattr(self, field_name)
            params[field_name] = _param_from_field(field_name, field_info, field_value)
        return params

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


def _default_eo_normalization_rules() -> NormalizationRules:
    from sources.config.airflow_params import EO_NORMALIZATION_RULES

    return EO_NORMALIZATION_RULES


def _default_eo_product_mapping() -> dict:
    from sources.config.airflow_params import get_mapping_config

    return get_mapping_config()


class EoSourceAirflowConfig(SourceConfig):
    """Éco-organismes standard (API pointsapport Ademe)."""

    normalization_rules: NormalizationRules = Field(
        default_factory=_default_eo_normalization_rules,
        description="Règles de normalisation EO (EO_NORMALIZATION_RULES par défaut).",
    )
    product_mapping: dict = Field(
        default_factory=_default_eo_product_mapping,
        description=(
            "Mapping produits / sous-catégories (get_mapping_config() par défaut)."
        ),
    )


class EoLabelBonusReparationSourceAirflowConfig(EoSourceAirflowConfig):
    label_bonus_reparation: Optional[str] = Field(
        default=None,
        description="Code label bonus réparation appliqué à la source.",
    )


class EoReturnableObjectsSourceAirflowConfig(EoSourceAirflowConfig):
    returnable_objects: bool = Field(
        default=False,
        description=(
            "Points d'apport de contenants consignés : associer le geste `rapporter` "
            "aux points ré-emploi."
        ),
    )


class SinoeSourceAirflowConfig(SourceConfig):
    dechet_mapping: dict = Field(
        default_factory=dict,
        description="Mapping déchets SINOE → sous-catégories LVAO.",
    )


class S3SourceAirflowConfig(SourceConfig):
    s3_connection_id: str | None = Field(
        default=None,
        description="ID de la connexion S3 (sources fichier S3 uniquement).",
    )


class CmaSourceAirflowConfig(SourceConfig):
    ignore_rows_with_null_or_empty_fields: list[str] = Field(
        default_factory=list,
        description=(
            "Champs source (avant normalisation) : si l'un est null ou vide, "
            "la ligne est ignorée après téléchargement."
        ),
    )


class OcabSourceAirflowConfig(EoSourceAirflowConfig):
    oca: OCAConfig | None = Field(
        default=None,
        description="Configuration spécifique OCA (préfixe, déduplication).",
    )


def _normalization_rules_to_airflow_json(
    rules: list[Any],
) -> str:
    serialized = [
        rule.model_dump() if isinstance(rule, BaseModel) else rule for rule in rules
    ]
    return json.dumps(serialized)


def _param_from_field(field_name: str, field_info, field_value: Any) -> Param:
    if field_name == "normalization_rules":
        return Param(
            default=_normalization_rules_to_airflow_json(field_value),
            type="string",
            description_md=field_info.description,
        )

    if field_name in {"product_mapping", "dechet_mapping"}:
        param_kwargs: dict[str, Any] = {"default": field_value}
        if field_info.description:
            param_kwargs["description_md"] = field_info.description
        return Param(**param_kwargs)

    if field_name == "oca":
        default = field_value.model_dump() if field_value is not None else None
        param_kwargs = {"default": default}
        if field_info.description:
            param_kwargs["description_md"] = field_info.description
        return Param(**param_kwargs)

    assert field_info.annotation is not None
    param = {
        "default": field_value,
        "type": _airflow_type_for_annotation(field_info.annotation),
        "description_md": field_info.description,
    }
    for extra_name in EXTRA_ATTRIBUTES:
        if extra_value := getattr(field_info, extra_name, None):
            param[extra_name] = extra_value
        elif field_info.json_schema_extra and (
            extra_value := field_info.json_schema_extra.get(extra_name, None)
        ):
            param[extra_name] = extra_value
    return Param(**param)


def _airflow_type_for_annotation(annotation: Any) -> Any:
    if annotation in PYDANTIC_TYPE_TO_AIRFLOW_TYPE:
        return PYDANTIC_TYPE_TO_AIRFLOW_TYPE[annotation]
    origin = get_origin(annotation)
    if origin in (Union, types.UnionType):
        args = get_args(annotation)
        non_none = [arg for arg in args if arg is not type(None)]
        if len(non_none) == 1 and type(None) in args:
            optional = Optional[non_none[0]]
            if optional in PYDANTIC_TYPE_TO_AIRFLOW_TYPE:
                return PYDANTIC_TYPE_TO_AIRFLOW_TYPE[optional]
    raise KeyError(f"Type Airflow non géré pour l'annotation {annotation!r}")


def config_to_airflow_params(config: SourceConfig) -> dict[str, Param]:
    """Alias module (comme enrich) ; préférer `config.to_airflow_params()`."""
    return config.to_airflow_params()


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
