from airflow.models import DAG
from airflow.operators.python import PythonOperator
from suggestions.tasks.business_logic.db_apply_suggestion import db_apply_suggestion


def db_apply_suggestion_task(dag: DAG):
    return PythonOperator(
        task_id="db_apply_suggestion_to_process",
        python_callable=db_apply_suggestion_wrapper,
        dag=dag,
    )


def db_apply_suggestion_wrapper(**kwargs):
    return db_apply_suggestion()
