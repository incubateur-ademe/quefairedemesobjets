from airflow.models import DAG
from airflow.operators.python import ShortCircuitOperator
from suggestions.tasks.business_logic.db_check_suggestion_to_process import (
    db_check_suggestion_to_process,
)


def db_check_suggestion_to_process_task(dag: DAG):
    return ShortCircuitOperator(
        task_id="db_check_suggestion_to_process",
        python_callable=db_check_suggestion_to_process,
        dag=dag,
    )
