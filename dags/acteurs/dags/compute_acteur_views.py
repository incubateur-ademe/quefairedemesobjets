from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from shared.config.schedules import SCHEDULES

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": pendulum.today("UTC").add(days=-1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
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
    schedule=SCHEDULES.DAILY,
    max_active_runs=1,
) as dag:
    dbt_run_base_acteurs = BashOperator(
        task_id="dbt_run_base_acteurs",
        bash_command=("cd /opt/airflow/dbt/ && dbt run --models base.acteurs"),
    )
    dbt_test_base_acteurs = BashOperator(
        task_id="dbt_test_base_acteurs",
        bash_command=("cd /opt/airflow/dbt/ && dbt test --models base.acteurs"),
    )
    dbt_run_intermediate_acteurs = BashOperator(
        task_id="dbt_run_intermediate_acteurs",
        bash_command=("cd /opt/airflow/dbt/ && dbt run --models intermediate.acteurs"),
    )
    dbt_test_intermediate_acteurs = BashOperator(
        task_id="dbt_test_intermediate_acteurs",
        bash_command=("cd /opt/airflow/dbt/ && dbt test --models intermediate.acteurs"),
    )

    dbt_run_marts_acteurs_exhaustive = BashOperator(
        task_id="dbt_run_marts_acteurs_exhaustive",
        bash_command=(
            "cd /opt/airflow/dbt/ && dbt run --models marts.acteurs.exhaustive"
        ),
    )
    dbt_test_marts_acteurs_exhaustive = BashOperator(
        task_id="dbt_test_marts_acteurs_exhaustive",
        bash_command=(
            "cd /opt/airflow/dbt/ && dbt test --models marts.acteurs.exhaustive"
        ),
    )
    dbt_run_exposure_acteurs_exhaustive = BashOperator(
        task_id="dbt_run_exposure_acteurs_exhaustive",
        bash_command=(
            "cd /opt/airflow/dbt/ && dbt run --models exposure.acteurs.exhaustive"
        ),
    )
    dbt_test_exposure_acteurs_exhaustive = BashOperator(
        task_id="dbt_test_exposure_acteurs_exhaustive",
        bash_command=(
            "cd /opt/airflow/dbt/ && dbt test --models exposure.acteurs.exhaustive"
        ),
    )

    dbt_run_marts_acteurs_carte = BashOperator(
        task_id="dbt_run_marts_acteurs_carte",
        bash_command=("cd /opt/airflow/dbt/ && dbt run --models marts.acteurs.carte"),
    )
    dbt_test_marts_acteurs_carte = BashOperator(
        task_id="dbt_test_marts_acteurs_carte",
        bash_command=("cd /opt/airflow/dbt/ && dbt test --models marts.acteurs.carte"),
    )
    dbt_run_exposure_acteurs_carte = BashOperator(
        task_id="dbt_run_exposure_acteurs_carte",
        bash_command=(
            "cd /opt/airflow/dbt/ && dbt run --models exposure.acteurs.carte"
        ),
    )
    dbt_test_exposure_acteurs_carte = BashOperator(
        task_id="dbt_test_exposure_acteurs_carte",
        bash_command=(
            "cd /opt/airflow/dbt/ && dbt test --models exposure.acteurs.carte"
        ),
    )

    dbt_run_marts_acteurs_opendata = BashOperator(
        task_id="dbt_run_marts_acteurs_opendata",
        bash_command=(
            "cd /opt/airflow/dbt/ && dbt run --models marts.acteurs.opendata"
        ),
    )
    dbt_test_marts_acteurs_opendata = BashOperator(
        task_id="dbt_test_marts_acteurs_opendata",
        bash_command=(
            "cd /opt/airflow/dbt/ && dbt test --models marts.acteurs.opendata"
        ),
    )
    dbt_run_exposure_acteurs_opendata = BashOperator(
        task_id="dbt_run_exposure_acteurs_opendata",
        bash_command=(
            "cd /opt/airflow/dbt/ && dbt run --models exposure.acteurs.opendata"
        ),
    )
    dbt_test_exposure_acteurs_opendata = BashOperator(
        task_id="dbt_test_exposure_acteurs_opendata",
        bash_command=(
            "cd /opt/airflow/dbt/ && dbt test --models exposure.acteurs.opendata"
        ),
    )

    # Définir la séquence principale
    (
        dbt_run_base_acteurs
        >> dbt_test_base_acteurs
        >> dbt_run_intermediate_acteurs
        >> dbt_test_intermediate_acteurs
        # Branche exhaustive
        >> dbt_run_marts_acteurs_exhaustive
        >> dbt_test_marts_acteurs_exhaustive
        >> dbt_run_exposure_acteurs_exhaustive
        >> dbt_test_exposure_acteurs_exhaustive
        # Branche carte
        >> dbt_run_marts_acteurs_carte
        >> dbt_test_marts_acteurs_carte
        >> dbt_run_exposure_acteurs_carte
        >> dbt_test_exposure_acteurs_carte
        # Branche opendata
        >> dbt_run_marts_acteurs_opendata
        >> dbt_test_marts_acteurs_opendata
        >> dbt_run_exposure_acteurs_opendata
        >> dbt_test_exposure_acteurs_opendata
    )
