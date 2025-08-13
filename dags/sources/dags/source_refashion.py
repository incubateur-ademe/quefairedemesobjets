from airflow import DAG
from shared.config.tags import TAGS
from sources.config.airflow_params import EO_NORMALIZATION_RULES, get_mapping_config
from sources.tasks.airflow_logic.operators import (
    default_args,
    default_params,
    eo_task_chain,
)

with DAG(
    dag_id="eo-refashion",
    dag_display_name="Source - REFASHION",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for Refashion dataset"
    ),
    tags=[
        TAGS.SOURCE,
        TAGS.DATA_POINTSAPPORT_ADEME,
        TAGS.ECO_ORGANISME,
        TAGS.REFASHION,
        TAGS.TLC,
    ],
    **default_params,
    params={
        "normalization_rules": EO_NORMALIZATION_RULES,
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-refashion/lines?size=10000"
        ),
        "metadata_endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-refashion/schema"
        ),
        "validate_address_with_ban": False,
        "label_bonus_reparation": "refashion",
        "product_mapping": get_mapping_config(),
    },
) as dag:
    eo_task_chain(dag)
