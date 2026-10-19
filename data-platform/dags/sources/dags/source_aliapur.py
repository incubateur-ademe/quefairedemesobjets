from airflow import DAG
from shared.config.airflow import DEFAULT_ARGS
from shared.config.tags import TAGS
from sources.config.models import EoSourceAirflowConfig
from sources.tasks.airflow_logic.operators import default_params, eo_task_chain

with DAG(
    dag_id="eo-aliapur",
    dag_display_name="Source - ALIAPUR",
    default_args=DEFAULT_ARGS,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for Aliapur dataset"
    ),
    tags=[
        TAGS.SOURCE,
        TAGS.DATA_POINTSAPPORT_ADEME,
        TAGS.ECO_ORGANISME,
        TAGS.ALIAPUR,
        TAGS.PNEU,
    ],
    **default_params,
    params=EoSourceAirflowConfig(
        endpoint=(
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-aliapur/lines?size=10000"
        ),
        metadata_endpoint=(
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-aliapur/schema"
        ),
    ).to_airflow_params(),
) as dag:
    eo_task_chain(dag)
