from airflow import DAG
from shared.config.tags import TAGS
from sources.config.airflow_params import EO_NORMALIZATION_RULES, get_mapping_config
from sources.tasks.airflow_logic.operators import (
    default_args,
    default_params,
    eo_task_chain,
)

with DAG(
    dag_id="eo-corepile",
    dag_display_name="Source - COREPILE",
    default_args=default_args,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for Corepile dataset"
    ),
    tags=[
        TAGS.SOURCE,
        TAGS.DATA_POINTSAPPORT_ADEME,
        TAGS.ECO_ORGANISME,
        TAGS.COREPILE,
        TAGS.PA,
    ],
    **default_params,
    params={
        "normalization_rules": EO_NORMALIZATION_RULES,
        "endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-corepile-ecosystem/lines?size=10000"
        ),
        "metadata_endpoint": (
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-corepile-ecosystem/schema"
        ),
        "validate_address_with_ban": False,
        "product_mapping": get_mapping_config(),
    },
) as dag:
    eo_task_chain(dag)
