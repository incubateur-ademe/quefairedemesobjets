from airflow import DAG
from shared.config.airflow import DEFAULT_ARGS
from shared.config.tags import TAGS
from sources.config.models import EoReturnableObjectsSourceAirflowConfig
from sources.tasks.airflow_logic.operators import default_params, eo_task_chain

with DAG(
    dag_id="eo-citeo",
    dag_display_name="Source - CITEO",
    default_args=DEFAULT_ARGS,
    description=(
        "Injestion des données de l'éco-organisme CITEO à partir des données disponible"
        " sur de Koumoul"
    ),
    tags=[
        TAGS.SOURCE,
        TAGS.DATA_POINTSAPPORT_ADEME,
        TAGS.ECO_ORGANISME,
        TAGS.CITEO,
        TAGS.EMPAP,
    ],
    **default_params,
    params=EoReturnableObjectsSourceAirflowConfig(
        endpoint=(
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-citeo/lines?size=10000"
        ),
        metadata_endpoint=(
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-citeo/schema"
        ),
        returnable_objects=True,
    ).to_airflow_params(),
) as dag:
    eo_task_chain(dag)
