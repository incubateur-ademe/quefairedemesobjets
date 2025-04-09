"""Read data from DB needed for RGPD anonymization"""

import logging

from airflow import DAG
from airflow.exceptions import AirflowSkipException
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from enrich.config import DBT, TASKS, XCOMS, xcom_pull

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""
    ============================================================
    Description de la tâche "{TASKS.ENRICH_DBT_MODELS_REFRESH}"
    ============================================================
    💡 quoi: lecture des données via le modèle DBT
    {DBT.MARTS_ENRICH_AE_RGPD}

    🎯 pourquoi: faire un pré-filtre sur les matches potentiels
    (pas récupérer les ~27M de lignes de la table AE unite_legale)

    🏗️ comment: on récupère uniquement les matches SIREN avec
    des infos de noms/prénoms dans l'AE en passant par de la normalisation
    de chaines de caractères
    """


def enrich_dbt_models_refresh_wrapper(ti) -> None:
    logger.info(task_info_get())

    # Config
    config = xcom_pull(ti, XCOMS.CONFIG)
    logger.info(f"📖 Configuration:\n{config.model_dump_json(indent=2)}")

    if not config.dbt_models_refresh:
        raise AirflowSkipException("🚫 Rafraîchissement des modèles DBT désactivé")

    logger.info(
        f"🔄 Rafraîchissement des modèles DBT: {config.dbt_models_refresh_command}"
    )
    bash = BashOperator(
        task_id=TASKS.ENRICH_DBT_MODELS_REFRESH + "_bash",
        bash_command=config.dbt_build_command,
    )
    bash.execute(context=ti.get_template_context())


def enrich_dbt_models_refresh_task(
    dag: DAG,
) -> PythonOperator:
    return PythonOperator(
        task_id=TASKS.ENRICH_DBT_MODELS_REFRESH,
        python_callable=enrich_dbt_models_refresh_wrapper,
        dag=dag,
    )
