import json

from airflow import DAG
from airflow.sdk.definitions.param import ParamsDict
from shared.config.airflow import DEFAULT_ARGS
from shared.config.tags import TAGS
from sources.config.airflow_params import EO_NORMALIZATION_RULES, get_mapping_config
from sources.tasks.airflow_logic.operators import default_params, eo_task_chain

with DAG(
    dag_id="eo-batribox",
    dag_display_name="Source - BATRIBOX",
    default_args=DEFAULT_ARGS,
    description=(
        "Injestion des données de l'éco-organisme BATRIBOX à partir des données"
        " disponibles sur de Koumoul"
    ),
    tags=[
        TAGS.SOURCE,
        TAGS.DATA_POINTSAPPORT_ADEME,
        TAGS.ECO_ORGANISME,
        TAGS.BATRIBOX,
        TAGS.PA,
    ],
    **default_params,
    params=ParamsDict(
        {
            "endpoint": (
                "https://data.ademe.fr/data-fair/api/v1/datasets/"
                "donnees-eo-batribox/lines?size=10000"
            ),
            "metadata_endpoint": (
                "https://data.ademe.fr/data-fair/api/v1/datasets/"
                "donnees-eo-batribox/schema"
            ),
            "normalization_rules": json.dumps(
                EO_NORMALIZATION_RULES
                + [
                    {
                        "column": "source_code",
                        "value": "batribox",
                    }
                ]
            ),
            "validate_address_with_ban": False,
            "product_mapping": get_mapping_config("sous_categories"),
            "use_legacy_suggestions": True,
        }
    ),
) as dag:
    eo_task_chain(dag)
