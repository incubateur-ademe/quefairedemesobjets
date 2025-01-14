from airflow.models import DAG
from airflow.operators.python import ShortCircuitOperator
from suggestions.business_logic.db_read_suggestiontoprocess import (
    db_read_suggestiontoprocess,
)


def db_read_suggestiontoprocess_task(dag: DAG):
    return ShortCircuitOperator(
        task_id="check_suggestion_to_process",
        python_callable=db_read_suggestiontoprocess,
        dag=dag,
    )
