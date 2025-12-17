from acteurs.tasks.airflow_logic.check_not_prod_env import check_isnt_prod_env_task
from acteurs.tasks.airflow_logic.copy_db_task import (
    copy_db_data_task,
    copy_db_schema_task,
)
from airflow.decorators import dag
from airflow.models.baseoperator import chain
from airflow.operators.bash import BashOperator
from shared.config.airflow import DEFAULT_ARGS
from shared.config.dbt_commands import DBT_RUN, DBT_TEST
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS


@dag(
    dag_id="compute_sample_acteur",
    default_args=DEFAULT_ARGS,
    schedule=SCHEDULES.EVERY_DAY_AT_00_00,
    start_date=START_DATES.DEFAULT,
    dag_display_name="[TEST] Calculer l'échantillon des acteurs",
    description=("Ce DAG construit l'échantillon des acteurs utilisables pour tester"),
    tags=[TAGS.TEST, TAGS.ACTEURS, TAGS.DBT],
    max_active_runs=1,
)
def compute_sample_acteur():

    check_prod_env = check_isnt_prod_env_task()

    dbt_run_base_acteurs = BashOperator(
        task_id="dbt_run_base_acteurs",
        bash_command=(f"{DBT_RUN} tag:acteurs,tag:sample"),
    )
    dbt_test_base_acteurs = BashOperator(
        task_id="dbt_test_base_acteurs",
        bash_command=(f"{DBT_TEST} tag:acteurs,tag:sample"),
    )

    chain(
        check_prod_env,
        dbt_run_base_acteurs,
        dbt_test_base_acteurs,
        copy_db_schema_task(),
        copy_db_data_task(),
    )


dag = compute_sample_acteur()
