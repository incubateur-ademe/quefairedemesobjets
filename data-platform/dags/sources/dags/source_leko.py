from airflow import DAG
from shared.config.airflow import DEFAULT_ARGS
from shared.config.tags import TAGS
from sources.config.models import EoReturnableObjectsSourceAirflowConfig
from sources.tasks.airflow_logic.operators import default_params, eo_task_chain

with DAG(
    dag_id="eo-leko",
    dag_display_name="Source - LEKO",
    default_args=DEFAULT_ARGS,
    description=(
        "Ingestion des données de l'éco-organisme LEKO à partir des données disponibles"
        " sur de Koumoul"
    ),
    tags=[
        TAGS.SOURCE,
        TAGS.DATA_POINTSAPPORT_ADEME,
        TAGS.ECO_ORGANISME,
        TAGS.LEKO,
        TAGS.EMPAP,
    ],
    **default_params,
    params=EoReturnableObjectsSourceAirflowConfig(
        endpoint=(
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-leko/lines?size=10000"
        ),
        metadata_endpoint=(
            "https://data.pointsapport.ademe.fr/data-fair/api/v1/datasets/"
            "donnees-eo-leko/schema"
        ),
        returnable_objects=True,
    ).to_airflow_params(),
) as dag:
    eo_task_chain(dag)
