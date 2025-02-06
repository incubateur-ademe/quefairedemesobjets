"""
Tâche Airflow pour valider la configuration de clustering
"""

import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from cluster.config.model import ClusterConfig
from utils import logging_utils as log
from utils.django import django_model_fields_attributes_get, django_setup_full

django_setup_full()

from qfdmo.models import Acteur, ActeurType, Source  # noqa: E402

logger = logging.getLogger(__name__)


def task_info_get():
    return """


    ============================================================
    Description de la tâche "cluster_acteurs_config_create"
    ============================================================

    💡 quoi: valide la configuration fournie par la UI (+ défauts si il y en a)

    🎯 pourquoi: échouer au plus tôt si il y a des problèmes de conf et ne pas
        faire du traitement de données inutile

    🏗️ comment: en comparant la config fournie avec des règles censées
        s'aligner avec les besoins métier (ex: prérequis)
        et la UI (ex: optionalité)
    """


def cluster_acteurs_config_create_wrapper(**kwargs):
    """Wrapper de la tâche Airflow pour créer une configuration à
    partir des params du DAG + autre logique métier / valeurs DB."""
    logger.info(task_info_get())
    params = kwargs["params"]
    extra = {
        "fields_all": django_model_fields_attributes_get(Acteur),
        "mapping_source_ids_by_codes": {x.code: x.id for x in Source.objects.all()},
        "mapping_acteur_type_ids_by_codes": {
            x.code: x.id for x in ActeurType.objects.all()
        },
    }
    config = ClusterConfig(**(params | extra))
    log.preview("Config", config)
    kwargs["ti"].xcom_push(key="config", value=config)


def cluster_acteurs_config_create_task(dag: DAG) -> PythonOperator:
    """La tâche Airflow qui ne fait que appeler le wrapper"""
    return PythonOperator(
        task_id="cluster_acteurs_config_create",
        python_callable=cluster_acteurs_config_create_wrapper,
        dag=dag,
    )
