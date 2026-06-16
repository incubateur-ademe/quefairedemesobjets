import logging

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from shared.config.airflow import DEFAULT_ARGS_NO_RETRIES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS
from utils.django import django_setup_full

# Load Django environement to test Django and saving airflow logs to s3 storage are
# compatible
django_setup_full()

logger = logging.getLogger(__name__)


def test_django_and_logs():
    logger.info("Test Django and Logs")


with DAG(
    dag_id="test_logs_pushed_to_s3",
    dag_display_name="[TEST] Les logs Airflow sont enregistrés sur s3",
    tags=[TAGS.DEV_TOOLS],
    default_args=DEFAULT_ARGS_NO_RETRIES,
    schedule=None,
    start_date=START_DATES.DEFAULT,
    description=(
        """
Lancer le DAG et vérifier que les logs sont disponibles sur s3
La mention `Found logs in s3` doit apparaitre dans les logs de la tâche
"""
    ),
) as dag:
    PythonOperator(
        task_id="test_django_and_logs",
        python_callable=test_django_and_logs,
        op_kwargs={"table_name": "qfdmo_acteur"},
        dag=dag,
    )
