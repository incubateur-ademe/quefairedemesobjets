import logging

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from cluster.tasks.airflow_logic.task_ids import (
    TASK_PARENTS_CHOOSE_NEW,
    TASK_SUGGESTIONS_DISPLAY,
)
from cluster.tasks.business_logic.cluster_acteurs_suggestions.display import (
    cluster_acteurs_suggestions_display,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def task_info_get():
    return f"""


    ============================================================
    Description de la tâche "{TASK_SUGGESTIONS_DISPLAY}"
    ============================================================

    💡 quoi: affichage de l'état final des suggestions avant
    écriture en base

    🎯 pourquoi: avoir une vue d'ensemble au niveau airflow:
     - si on utilise le dry_un avant écriture
     - si quelque se passe mal au niveau de l'écriture en base

    🏗️ comment: pas de nouvelle données générées ici, on reprends
    juste les données des tâches précédentes qu'on essaye d'afficher
    de manière lisible
    """


def cluster_acteurs_suggestions_display_wrapper(**kwargs) -> None:
    logger.info(task_info_get())

    df: pd.DataFrame = kwargs["ti"].xcom_pull(
        key="df", task_ids=TASK_PARENTS_CHOOSE_NEW
    )
    # Not a Skip: we should never get here if we don't have data to work w/
    if df.empty:
        raise ValueError("Pas de données clusters récupérées")

    suggestions = cluster_acteurs_suggestions_display(df)

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    for suggestion in suggestions:
        cluster_id = suggestion["cluster_id"]
        df_changes = pd.DataFrame(suggestion["changes"])
        log.preview_df_as_markdown(
            f"Suggestion pour cluster_id={cluster_id}", df_changes
        )

    kwargs["ti"].xcom_push(key="suggestions", value=suggestions)


def cluster_acteurs_suggestions_display_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id=TASK_SUGGESTIONS_DISPLAY,
        python_callable=cluster_acteurs_suggestions_display_wrapper,
        dag=dag,
    )
