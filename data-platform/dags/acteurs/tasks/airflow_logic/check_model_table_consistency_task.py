"""Performs crawl checks on the URLs"""

import logging

from acteurs.tasks.business_logic.check_model_table_consistency import (
    check_model_table_consistency,
)
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk.exceptions import AirflowFailException
from utils import logging_utils as log

logger = logging.getLogger(__name__)

TASK_NAME = "check_model_table_consistency"


def task_info_get(model_name, table_name):
    return f"""
    ============================================================
    Description de la tâche "{TASK_NAME}"
    ============================================================
    💡 quoi: Vérifier que le schema table correspond au model

    🎯 pourquoi:

    🏗️ comment: La fonction compare_model_vs_table parcours les champs du model
    {model_name} et les comparent aux champs de la table {table_name}
    """


def check_model_table_consistency_wrapper(
    ti, params, *, django_app: str, model_name: str, table_name: str
) -> None:
    # model_name = "DisplayedActeur"
    # table_name = "exposure_carte_acteur"
    logger.info(task_info_get(model_name, table_name))

    log.preview("Modèle Django", model_name)
    log.preview("Table", table_name)
    if not check_model_table_consistency(
        django_app=django_app,
        model_name=model_name,
        table_name=table_name,
    ):
        raise AirflowFailException(
            f"le modèle {model_name} ne correspond pas à la table {table_name}"
        )


def check_model_table_consistency_task(
    django_app: str,
    model_name: str,
    table_name: str,
) -> PythonOperator:
    task_name = f"check_{model_name}_vs_{table_name}_consistency"
    return PythonOperator(
        task_id=task_name,
        python_callable=check_model_table_consistency_wrapper,
        op_kwargs={
            "django_app": django_app,
            "model_name": model_name,
            "table_name": table_name,
        },
    )
