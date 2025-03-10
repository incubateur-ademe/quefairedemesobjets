from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 2, 14),
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
    schedule=None,
    max_active_runs=1,
) as dag:
    """
    Run DBT models
    dbt run --models base
    dbt test --models base

    dbt run --models intermediate
    dbt test --models intermediate

    dbt run --models marts.exhaustive
    dbt test --models marts.exhaustive
    dbt run --models marts.carte
    dbt test --models marts.carte
    dbt run --models marts.opendata
    dbt test --models marts.opendata

    dbt run --models exposure.exhaustive
    dbt test --models exposure.exhaustive
    dbt run --models exposure.carte
    dbt test --models exposure.carte
    dbt run --models exposure.opendata
    dbt test --models exposure.opendata

    """
    dbt_run_base = BashOperator(
        task_id="run_base",
        bash_command=("cd /opt/airflow/dbt/ && dbt run --models base"),
        dag=dag,
    )
    dbt_test_base = BashOperator(
        task_id="test_base",
        bash_command=("cd /opt/airflow/dbt/ && dbt test --models base"),
        #        dag=dag,
    )

    dbt_run_intermediate = BashOperator(
        task_id="run_intermediate",
        bash_command=("cd /opt/airflow/dbt/ && dbt run --models intermediate"),
        #        dag=dag,
    )
    dbt_test_intermediate = BashOperator(
        task_id="test_intermediate",
        bash_command=("cd /opt/airflow/dbt/ && dbt test --models intermediate"),
        #        dag=dag,
    )

    dbt_run_marts_exhaustive = BashOperator(
        task_id="run_marts_exhaustive",
        bash_command=("cd /opt/airflow/dbt/ && dbt run --models marts.exhaustive"),
        #        dag=dag,
    )
    dbt_test_marts_exhaustive = BashOperator(
        task_id="test_marts_exhaustive",
        bash_command=("cd /opt/airflow/dbt/ && dbt test --models marts.exhaustive"),
        #        dag=dag,
    )
    dbt_run_exposure_exhaustive = BashOperator(
        task_id="run_exposure_exhaustive",
        bash_command=("cd /opt/airflow/dbt/ && dbt run --models exposure.exhaustive"),
        #        dag=dag,
    )
    dbt_test_exposure_exhaustive = BashOperator(
        task_id="test_exposure_exhaustive",
        bash_command=("cd /opt/airflow/dbt/ && dbt test --models exposure.exhaustive"),
        #        dag=dag,
    )

    dbt_run_marts_carte = BashOperator(
        task_id="run_marts_carte",
        bash_command=("cd /opt/airflow/dbt/ && dbt run --models marts.carte"),
        #        dag=dag,
    )
    dbt_test_marts_carte = BashOperator(
        task_id="test_marts_carte",
        bash_command=("cd /opt/airflow/dbt/ && dbt test --models marts.carte"),
        #        dag=dag,
    )
    dbt_run_exposure_carte = BashOperator(
        task_id="run_exposure_carte",
        bash_command=("cd /opt/airflow/dbt/ && dbt run --models exposure.carte"),
        #        dag=dag,
    )
    dbt_test_exposure_carte = BashOperator(
        task_id="test_exposure_carte",
        bash_command=("cd /opt/airflow/dbt/ && dbt test --models exposure.carte"),
        #        dag=dag,
    )

    dbt_run_marts_opendata = BashOperator(
        task_id="run_marts_opendata",
        bash_command=("cd /opt/airflow/dbt/ && dbt run --models marts.opendata"),
        #        dag=dag,
    )
    dbt_test_marts_opendata = BashOperator(
        task_id="test_marts_opendata",
        bash_command=("cd /opt/airflow/dbt/ && dbt test --models marts.opendata"),
        #        dag=dag,
    )
    dbt_run_exposure_opendata = BashOperator(
        task_id="run_exposure_opendata",
        bash_command=("cd /opt/airflow/dbt/ && dbt run --models exposure.opendata"),
        #        dag=dag,
    )
    dbt_test_exposure_opendata = BashOperator(
        task_id="test_exposure_opendata",
        bash_command=("cd /opt/airflow/dbt/ && dbt test --models exposure.opendata"),
        #        dag=dag,
    )

    # Définir la séquence principale
    dbt_run_base >> dbt_test_base >> dbt_run_intermediate >> dbt_test_intermediate

    # Après intermediate, brancher en parallèle
    # Branche exhaustive
    (
        dbt_test_intermediate
        >> dbt_run_marts_exhaustive
        >> dbt_test_marts_exhaustive
        >> dbt_run_exposure_exhaustive
        >> dbt_test_exposure_exhaustive
    )

    # Branche carte
    (
        dbt_test_intermediate
        >> dbt_run_marts_carte
        >> dbt_test_marts_carte
        >> dbt_run_exposure_carte
        >> dbt_test_exposure_carte
    )

    # Branche opendata
    (
        dbt_test_intermediate
        >> dbt_run_marts_opendata
        >> dbt_test_marts_opendata
        >> dbt_run_exposure_opendata
        >> dbt_test_exposure_opendata
    )
    # chain(
    #     dbt_run_base,
    #     dbt_test_base,
    #     dbt_run_intermediate,
    #     dbt_test_intermediate,
    #     [
    #         chain(
    #             dbt_run_marts_exhaustive,
    #             dbt_test_marts_exhaustive,
    #             dbt_run_exposure_exhaustive,
    #             dbt_test_exposure_exhaustive,
    #         ),
    #         chain(
    #             dbt_run_marts_carte,
    #             dbt_test_marts_carte,
    #             dbt_run_exposure_carte,
    #             dbt_test_exposure_carte,
    #         ),
    #         chain(
    #             dbt_run_marts_opendata,
    #             dbt_test_marts_opendata,
    #             dbt_run_exposure_opendata,
    #             dbt_test_exposure_opendata,
    #         ),
    #     ],
    # )
