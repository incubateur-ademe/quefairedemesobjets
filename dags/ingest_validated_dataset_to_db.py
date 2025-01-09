from datetime import timedelta

import pandas as pd
from airflow.models import DAG
from airflow.operators.python import PythonOperator, ShortCircuitOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago
from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from sources.config import shared_constants as constants
from utils import dag_ingest_validated_utils

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    dag_id="validate_and_process_suggestions",
    dag_display_name="Traitement des cohortes de données validées",
    default_args=default_args,
    description="traiter les suggestions à traiter",
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
)


def _get_first_suggetsioncohorte_to_insert():
    hook = PostgresHook(postgres_conn_id="qfdmo_django_db")
    row = hook.get_first(
        f"""
        SELECT * FROM data_suggestioncohorte
        WHERE statut = '{constants.SUGGESTION_ATRAITER}'
        LIMIT 1
        """
    )
    return row


def check_suggestion_to_process(**kwargs):
    row = _get_first_suggetsioncohorte_to_insert()
    return bool(row)


def fetch_and_parse_data(**context):
    row = _get_first_suggetsioncohorte_to_insert()
    suggestion_cohorte_id = row[0]

    engine = PostgresConnectionManager().engine

    df_sql = pd.read_sql_query(
        f"""
        SELECT * FROM data_suggestionunitaire
        WHERE suggestion_cohorte_id = '{suggestion_cohorte_id}'
        """,
        engine,
    )

    df_acteur_to_create = df_sql[
        df_sql["type_action"] == constants.SUGGESTION_SOURCE_AJOUT
    ]
    df_acteur_to_update = df_sql[
        df_sql["type_action"] == constants.SUGGESTION_SOURCE_AJOUT
    ]
    df_acteur_to_delete = df_sql[
        df_sql["type_action"] == constants.SUGGESTION_SOURCE_SUPRESSION
    ]
    df_acteur_to_enrich = df_sql[
        df_sql["type_action"] == constants.SUGGESTION_ENRICHISSEMENT
    ]

    df_update_actor = df_sql[df_sql["type_action"] == "UPDATE_ACTOR"]

    if not df_acteur_to_create.empty:
        normalized_dfs = df_acteur_to_create["suggestion"].apply(pd.json_normalize)
        df_acteur = pd.concat(normalized_dfs.tolist(), ignore_index=True)
        return dag_ingest_validated_utils.handle_create_event(
            df_acteur, suggestion_cohorte_id, engine
        )
    if not df_acteur_to_update.empty:
        normalized_dfs = df_acteur_to_update["suggestion"].apply(pd.json_normalize)
        df_acteur = pd.concat(normalized_dfs.tolist(), ignore_index=True)
        return dag_ingest_validated_utils.handle_create_event(
            df_acteur, suggestion_cohorte_id, engine
        )
    if not df_acteur_to_delete.empty:
        normalized_dfs = df_acteur_to_delete["suggestion"].apply(pd.json_normalize)
        df_actors_update_actor = pd.concat(normalized_dfs.tolist(), ignore_index=True)
        status_repeated = (
            df_acteur_to_delete["statut"]
            .repeat(df_acteur_to_delete["suggestion"].apply(len))
            .reset_index(drop=True)
        )
        df_actors_update_actor["status"] = status_repeated

        return dag_ingest_validated_utils.handle_update_actor_event(
            df_actors_update_actor, suggestion_cohorte_id
        )

    if not df_acteur_to_enrich.empty:

        normalized_dfs = df_update_actor["suggestion"].apply(pd.json_normalize)
        df_actors_update_actor = pd.concat(normalized_dfs.tolist(), ignore_index=True)
        status_repeated = (
            df_update_actor["status"]
            .repeat(df_update_actor["suggestion"].apply(len))
            .reset_index(drop=True)
        )
        df_actors_update_actor["status"] = status_repeated

        return dag_ingest_validated_utils.handle_update_actor_event(
            df_actors_update_actor, suggestion_cohorte_id
        )
    return {
        "dag_run_id": suggestion_cohorte_id,
    }


def write_data_to_postgres(**kwargs):
    data_dict = kwargs["ti"].xcom_pull(task_ids="fetch_and_parse_data")
    # If data_set is empty, nothing to do
    dag_run_id = data_dict["dag_run_id"]
    engine = PostgresConnectionManager().engine
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


check_suggestion_to_process_task = ShortCircuitOperator(
    task_id="check_suggestion_to_process",
    python_callable=check_suggestion_to_process,
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

(
    check_suggestion_to_process_task
    >> fetch_parse_task
    >> write_to_postgres_task
    >> trigger_create_final_actors_dag
)
