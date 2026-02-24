from airflow.providers.standard.operators.python import PythonOperator
from suggestions.tasks.business_logic.db_apply_suggestion import db_apply_suggestion


def db_apply_suggestion_task(use_suggestion_groupe: bool = False):
    return PythonOperator(
        task_id="db_apply_suggestion_to_process",
        python_callable=db_apply_suggestion_wrapper,
        op_kwargs={"use_suggestion_groupe": use_suggestion_groupe},
    )


def db_apply_suggestion_wrapper(use_suggestion_groupe: bool = False, **kwargs):
    return db_apply_suggestion(use_suggestion_groupe=use_suggestion_groupe)
