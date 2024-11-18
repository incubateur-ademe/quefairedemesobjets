from datetime import timedelta

import pandas as pd
from airflow.models import DAG
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.operators.python_operator import BranchPythonOperator, PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago
from utils import dag_ingest_validated_utils, shared_constants

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    dag_id="validate_and_process_dagruns",
    dag_display_name="Traitement des cohortes de données validées",
    default_args=default_args,
    description="Check for VALIDATE in qfdmo_dagrun and process qfdmo_dagrunchange",
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
)


def _get_first_dagrun_to_insert():
    hook = PostgresHook(postgres_conn_id="qfdmo_django_db")
    # get first row from table qfdmo_dagrun with status TO_INSERT
    row = hook.get_first(
        f"SELECT * FROM qfdmo_dagrun WHERE status = '{shared_constants.TO_INSERT}'"
        " LIMIT 1"
    )
    return row


def check_for_validation(**kwargs):
    # get first row from table qfdmo_dagrun with status TO_INSERT
    row = _get_first_dagrun_to_insert()

    # Skip if row is None
    if row is None:
        return "skip_processing"
    return "fetch_and_parse_data"


def fetch_and_parse_data(**context):
    row = _get_first_dagrun_to_insert()
    dag_run_id = row[0]

    pg_hook = PostgresHook(postgres_conn_id="qfdmo_django_db")
    engine = pg_hook.get_sqlalchemy_engine()

    df_sql = pd.read_sql_query(
        f"SELECT * FROM qfdmo_dagrunchange WHERE dag_run_id = '{dag_run_id}'",
        engine,
    )

    df_create = df_sql[df_sql["change_type"] == "CREATE"]
    df_update_actor = df_sql[df_sql["change_type"] == "UPDATE_ACTOR"]

    if not df_create.empty:
        normalized_dfs = df_create["row_updates"].apply(pd.json_normalize)
        df_actors_create = pd.concat(normalized_dfs.tolist(), ignore_index=True)
        return dag_ingest_validated_utils.handle_create_event(
            df_actors_create, dag_run_id, engine
        )
    if not df_update_actor.empty:

        normalized_dfs = df_update_actor["row_updates"].apply(pd.json_normalize)
        df_actors_update_actor = pd.concat(normalized_dfs.tolist(), ignore_index=True)
        status_repeated = (
            df_update_actor["status"]
            .repeat(df_update_actor["row_updates"].apply(len))
            .reset_index(drop=True)
        )
        df_actors_update_actor["status"] = status_repeated

        return dag_ingest_validated_utils.handle_update_actor_event(
            df_actors_update_actor, dag_run_id
        )
    return {
        "dag_run_id": dag_run_id,
    }


def write_data_to_postgres(**kwargs):
    data_dict = kwargs["ti"].xcom_pull(task_ids="fetch_and_parse_data")
    # If data_set is empty, nothing to do
    dag_run_id = data_dict["dag_run_id"]
    pg_hook = PostgresHook(postgres_conn_id="qfdmo_django_db")
    engine = pg_hook.get_sqlalchemy_engine()
    if "actors" not in data_dict:
        with engine.begin() as connection:
            dag_ingest_validated_utils.update_dag_run_status(connection, dag_run_id)
        return
    df_actors = data_dict["actors"]
    df_labels = data_dict.get("labels")
    df_acteur_services = data_dict.get("acteur_services")
    df_pds = data_dict.get("pds")
    df_pdssc = data_dict.get("pds_sous_categories")
    dag_run_id = data_dict["dag_run_id"]
    change_type = data_dict.get("change_type", "CREATE")

    with engine.begin() as connection:
        if change_type == "CREATE":
            dag_ingest_validated_utils.handle_write_data_create_event(
                connection, df_actors, df_labels, df_acteur_services, df_pds, df_pdssc
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
    trigger_dag_id="compute_carte_acteur",
    dag=dag,
)

branch_task >> skip_processing_task
(
    branch_task
    >> fetch_parse_task
    >> write_to_postgres_task
    >> trigger_create_final_actors_dag
)
