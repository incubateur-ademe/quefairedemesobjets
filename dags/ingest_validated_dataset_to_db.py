from datetime import timedelta
from importlib import import_module
from pathlib import Path

import pandas as pd
from airflow.models import DAG
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.operators.python_operator import BranchPythonOperator, PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago

env = Path(__file__).parent.name
utils = import_module(f"{env}.utils.utils")
dag_ingest_validated_utils = import_module(f"{env}.utils.dag_ingest_validated_utils")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    utils.get_dag_name(__file__, "validate_and_process_dagruns"),
    default_args=default_args,
    description="Check for VALIDATE in qfdmo_dagrun and process qfdmo_dagrunchange",
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
)


def check_for_validation(**kwargs):
    hook = PostgresHook(postgres_conn_id=utils.get_db_conn_id(__file__))
    row = hook.get_records(
        "SELECT EXISTS "
        "(SELECT 1 FROM qfdmo_dagrun WHERE status = 'DagRunStatus.TO_INSERT')"
    )
    return "fetch_and_parse_data" if row[0][0] else "skip_processing"


def fetch_and_parse_data(**context):
    pg_hook = PostgresHook(postgres_conn_id=utils.get_db_conn_id(__file__))
    engine = pg_hook.get_sqlalchemy_engine()

    df_sql = pd.read_sql_query(
        "SELECT * FROM qfdmo_dagrunchange WHERE "
        "dag_run_id IN "
        "(SELECT id FROM qfdmo_dagrun WHERE status = 'DagRunStatus.TO_INSERT')",
        engine,
    )

    # Pourquoi on ne prend que le premier élément de la liste ?
    dag_run_id = df_sql["dag_run_id"].iloc[0]

    change_type = df_sql["change_type"].iloc[0]

    normalized_dfs = df_sql["row_updates"].apply(pd.json_normalize)
    df_actors = pd.concat(normalized_dfs.tolist(), ignore_index=True)

    if change_type == "CREATE":
        return dag_ingest_validated_utils.handle_create_event(
            df_actors, dag_run_id, engine
        )
    elif change_type == "UPDATE_ACTOR":
        return dag_ingest_validated_utils.handle_update_actor_event(
            df_actors, dag_run_id
        )


def write_data_to_postgres(**kwargs):
    data_dict = kwargs["ti"].xcom_pull(task_ids="fetch_and_parse_data")
    df_actors = data_dict["actors"]
    df_labels = data_dict.get("labels")
    df_pds = data_dict.get("pds")
    df_pdssc = data_dict.get("pds_sous_categories")
    dag_run_id = data_dict["dag_run_id"]
    change_type = data_dict.get("change_type", "CREATE")
    pg_hook = PostgresHook(postgres_conn_id=utils.get_db_conn_id(__file__))
    engine = pg_hook.get_sqlalchemy_engine()

    with engine.begin() as connection:
        if change_type == "CREATE":
            dag_ingest_validated_utils.handle_write_data_create_event(
                connection, df_actors, df_labels, df_pds, df_pdssc
            )
        elif change_type == "UPDATE_ACTOR":
            dag_ingest_validated_utils.handle_write_data_update_actor_event(
                connection, df_actors
            )

        dag_ingest_validated_utils.update_dag_run_status(connection, dag_run_id)


fetch_parse_task = PythonOperator(
    task_id="fetch_and_parse_data",
    python_callable=fetch_and_parse_data,
    dag=dag,
)


def skip_processing(**kwargs):
    print("No records to validate. DAG run completes successfully.")


skip_processing_task = PythonOperator(
    task_id="skip_processing",
    python_callable=skip_processing,
    dag=dag,
)

branch_task = BranchPythonOperator(
    task_id="branch_processing",
    python_callable=check_for_validation,
    dag=dag,
)

write_to_postgres_task = PythonOperator(
    task_id="write_to_postgres",
    python_callable=write_data_to_postgres,
    dag=dag,
)

trigger_create_final_actors_dag = TriggerDagRunOperator(
    task_id="create_displayed_actors",
    trigger_dag_id=utils.get_dag_name(__file__, "apply_adresse_corrections"),
    dag=dag,
)

branch_task >> skip_processing_task
(
    branch_task
    >> fetch_parse_task
    >> write_to_postgres_task
    >> trigger_create_final_actors_dag
)
