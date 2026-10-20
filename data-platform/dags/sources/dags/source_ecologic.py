from airflow import DAG
from shared.config.airflow import DEFAULT_ARGS
from shared.config.tags import TAGS
from sources.config.airflow_params import get_mapping_config
from sources.config.models import EoSourceAirflowConfig
from sources.tasks.airflow_logic.operators import default_params, eo_task_chain

with DAG(
    dag_id="eo-ecologic",
    dag_display_name="Source - ECOLOGIC",
    default_args=DEFAULT_ARGS,
    description=(
        "A pipeline to fetch, process, and load to validate data into postgresql"
        " for Ecologic dataset"
    ),
    tags=[
        TAGS.SOURCE,
        TAGS.DATA_POINTSAPPORT_ADEME,
        TAGS.ECO_ORGANISME,
        TAGS.ECOLOGIC,
        TAGS.ABJ,
        TAGS.ASL,
        TAGS.EEE,
    ],
    **default_params,
    params=EoSourceAirflowConfig(
        endpoint=(
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-ecologic/lines?size=10000"
        ),
        metadata_endpoint=(
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-ecologic/schema"
        ),
        product_mapping=get_mapping_config(mapping_key="sous_categories_3eee"),
    ).to_airflow_params(),
) as dag:
    eo_task_chain(dag)
