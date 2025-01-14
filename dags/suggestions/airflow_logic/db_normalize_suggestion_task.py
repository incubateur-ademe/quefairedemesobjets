from airflow.models import DAG
from airflow.operators.python import PythonOperator
from suggestions.business_logic.db_normalize_suggestion import db_normalize_suggestion


def db_normalize_suggestion_task(dag: DAG):
    return PythonOperator(
        task_id="db_normalize_suggestion",
        python_callable=db_normalize_suggestion_wrapper,
        dag=dag,
    )


def db_normalize_suggestion_wrapper(**kwargs):
    return db_normalize_suggestion()
