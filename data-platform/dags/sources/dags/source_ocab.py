from airflow import DAG
from shared.config.airflow import DEFAULT_ARGS
from shared.config.tags import TAGS
from sources.config.models import OCAConfig, OcabSourceAirflowConfig
from sources.tasks.airflow_logic.operators import default_params, eo_task_chain

with DAG(
    dag_id="eo-ocab",
    dag_display_name="Source - OCAB",
    default_args=DEFAULT_ARGS,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for OCAB dataset"
    ),
    tags=[
        TAGS.SOURCE,
        TAGS.DATA_POINTSAPPORT_ADEME,
        TAGS.OCA,
        TAGS.OCAB,
        TAGS.PMCB,
    ],
    **default_params,
    params=OcabSourceAirflowConfig(
        endpoint=(
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-ocab/lines?size=10000"
        ),
        metadata_endpoint=(
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-ocab/schema"
        ),
        oca=OCAConfig(prefix="ocab", deduplication_source=True),
    ).to_airflow_params(),
) as dag:
    eo_task_chain(dag)
