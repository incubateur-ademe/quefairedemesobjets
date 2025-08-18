from airflow import DAG
from shared.config.tags import TAGS
from sources.config.airflow_params import EO_NORMALIZATION_RULES, get_mapping_config
from sources.tasks.airflow_logic.operators import (
    default_args,
    default_params,
    eo_task_chain,
)

with DAG(
    dag_id="eo-ocad3e",
    dag_display_name="Source - OCAD3E (ECOSYSTEM & ECOLOGIC) - label QualiRépar",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for OCAD3E dataset"
    ),
    tags=[
        TAGS.SOURCE,
        TAGS.DATA_POINTSAPPORT_ADEME,
        TAGS.OCA,
        TAGS.OCAD3E,
        TAGS.EEE,
    ],
    **default_params,
    params={
        "normalization_rules": EO_NORMALIZATION_RULES,
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-ocad3e/lines?size=10000"
        ),
        "metadata_endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-ocad3e/schema"
        ),
        "validate_address_with_ban": False,
        "label_bonus_reparation": "qualirepar",
        "product_mapping": get_mapping_config(mapping_key="sous_categories_qualirepar"),
    },
) as dag:
    eo_task_chain(dag)
