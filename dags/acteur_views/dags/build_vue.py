from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 2, 14),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "build_view_dag",
    default_args=default_args,
    dag_display_name="DBT - Rafraîchir les acteurs affichés",
    description=(
        "Ce DAG construit les tables des acteurs utilisables par l'admin"
        " (vue exhaustive des acteurs), par la carte (vue des acteurs affichés) et"
        " par l'export des acteurs en open-data."
    ),
    schedule=None,
    max_active_runs=1,
) as dag:

    run_dbt_exhaustive_acteurs_model = BashOperator(
        task_id="build_exhaustive_acteur",
        bash_command=(
            "cd /opt/airflow/dbt/ && dbt run --select qfdmo.exhaustive_acteurs"
        ),
        dag=dag,
    )
    test_dbt_exhaustive_acteurs_model = BashOperator(
        task_id="test_exhaustive_acteur",
        bash_command=(
            "cd /opt/airflow/dbt/ && dbt test --select qfdmo.exhaustive_acteurs"
        ),
        dag=dag,
    )
    run_dbt_carte_acteurs_model = BashOperator(
        task_id="build_exhaustive_acteur",
        bash_command=("cd /opt/airflow/dbt/ && dbt run --select qfdmo.carte_acteurs"),
        dag=dag,
    )
    test_dbt_carte_acteurs_model = BashOperator(
        task_id="test_exhaustive_acteur",
        bash_command=("cd /opt/airflow/dbt/ && dbt test --select qfdmo.carte_acteurs"),
        dag=dag,
    )
    (
        run_dbt_exhaustive_acteurs_model
        >> test_dbt_exhaustive_acteurs_model
        >> run_dbt_carte_acteurs_model
        >> test_dbt_carte_acteurs_model
    )
