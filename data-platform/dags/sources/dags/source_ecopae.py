import json

from airflow.sdk import DAG
from airflow.sdk.definitions.param import ParamsDict
from shared.config.airflow import DEFAULT_ARGS
from shared.config.tags import TAGS
from sources.config.airflow_params import EO_NORMALIZATION_RULES, get_mapping_config
from sources.tasks.airflow_logic.operators import default_params, eo_task_chain

with DAG(
    dag_id="eo-ecopae",
    dag_display_name="Source - ECOPAE",
    default_args=DEFAULT_ARGS,
    description=(
        "Injestion des données de l'éco-organisme ECOPAE à partir des données"
        " disponibles sur Koumoul"
    ),
    tags=[
        TAGS.SOURCE,
        TAGS.DATA_POINTSAPPORT_ADEME,
        TAGS.ECO_ORGANISME,
        TAGS.ECOPAE,
        TAGS.PCHIM,
    ],
    **default_params,
    params=ParamsDict(
        {
            "normalization_rules": json.dumps(EO_NORMALIZATION_RULES),
            "endpoint": (
                "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
                "donnees-eo-ecopae/lines?size=10000"
            ),
            "metadata_endpoint": (
                "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
                "donnees-eo-ecopae/schema"
            ),
            "validate_address_with_ban": False,
            "product_mapping": get_mapping_config(),
            "use_legacy_suggestions": True,
        }
    ),
) as dag:
    eo_task_chain(dag)
