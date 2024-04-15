from datetime import timedelta
from importlib import import_module
from pathlib import Path

import pandas as pd
from airflow.models import DAG
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago

env = Path(__file__).parent.name
utils = import_module(f"{env}.utils.utils")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "validate_and_process_dagruns",
    default_args=default_args,
    description="Check for VALIDATE in qfdmo_dagrun and process qfdmo_dagrunchange",
    schedule_interval="*/5 * * * *",
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

    max_id_pds = pd.read_sql_query(
        "SELECT max(id) FROM qfdmo_displayedpropositionservice", engine
    )["max"][0]
    df_sql = pd.read_sql_query(
        "SELECT * FROM qfdmo_dagrunchange WHERE "
        "dag_run_id IN "
        "(SELECT id FROM qfdmo_dagrun WHERE status = 'DagRunStatus.TO_INSERT')",
        engine,
    )
    dag_run_id = df_sql["dag_run_id"].iloc[0]

    normalized_dfs = df_sql["row_updates"].apply(pd.json_normalize)
    df_actors = pd.concat(normalized_dfs.tolist(), ignore_index=True)

    normalized_labels_dfs = df_actors["labels"].dropna().apply(pd.json_normalize)
    df_labels = pd.concat(normalized_labels_dfs.tolist(), ignore_index=True)

    normalized_pds_dfs = df_actors["proposition_services"].apply(pd.json_normalize)
    df_pds = pd.concat(normalized_pds_dfs.tolist(), ignore_index=True)
    ids_range = range(max_id_pds + 1, max_id_pds + 1 + len(df_pds))

    df_pds["id"] = ids_range
    df_pds["pds_sous_categories"] = df_pds.apply(
        lambda row: [
            {**d, "propositionservice_id": row["id"]}
            for d in row["pds_sous_categories"]
        ],
        axis=1,
    )

    normalized_pdssc_dfs = df_pds["pds_sous_categories"].apply(pd.json_normalize)
    df_pdssc = pd.concat(normalized_pdssc_dfs.tolist(), ignore_index=True)

    return {
        "actors": df_actors,
        "pds": df_pds[["id", "acteur_service_id", "action_id", "acteur_id"]],
        "pds_sous_categories": df_pdssc[
            ["propositionservice_id", "souscategorieobjet_id"]
        ],
        "dag_run_id": dag_run_id,
        "labels": df_labels[["acteur_id", "labelqualite_id"]],
    }


def write_data_to_postgres(**kwargs):
    data_dict = kwargs["ti"].xcom_pull(task_ids="fetch_and_parse_data")
    df_actors = data_dict["actors"]
    df_labels = data_dict["labels"]
    df_pds = data_dict["pds"]
    df_pdssc = data_dict["pds_sous_categories"]
    dag_run_id = data_dict["dag_run_id"]
    pg_hook = PostgresHook(postgres_conn_id=utils.get_db_conn_id(__file__))
    engine = pg_hook.get_sqlalchemy_engine()
    # TODO: For now assuming all events are CREATE events,
    #  so we remove the actors if they existe first
    with engine.begin() as connection:
        df_actors[
            [
                "identifiant_unique",
                "nom",
                "adresse",
                "adresse_complement",
                "code_postal",
                "ville",
                "url",
                "email",
                "location",
                "telephone",
                "nom_commercial",
                "siret",
                "identifiant_externe",
                "acteur_type_id",
                "statut",
                "source_id",
                "cree_le",
                "horaires_description",
                "modifie_le",
                "commentaires",
            ]
        ].to_sql("temp_actors", connection, if_exists="replace")

        delete_queries = [
            """
            DELETE FROM qfdmo_propositionservice_sous_categories
            WHERE propositionservice_id IN (
                SELECT id FROM qfdmo_propositionservice
                WHERE acteur_id IN (
                    SELECT identifiant_unique FROM temp_actors
                )
            );
            """,
            """
                 DELETE FROM qfdmo_acteur_labels
                  WHERE acteur_id IN (
                         SELECT identifiant_unique FROM temp_actors
                      );
            """,
            """
            DELETE FROM qfdmo_propositionservice
            WHERE acteur_id IN (
                SELECT identifiant_unique FROM temp_actors
            );
            """,
            """
            DELETE FROM qfdmo_acteur WHERE identifiant_unique
            in ( select identifiant_unique from temp_actors);
            """,
        ]

        for query in delete_queries:
            connection.execute(query)
        df_actors[
            [
                "identifiant_unique",
                "nom",
                "adresse",
                "adresse_complement",
                "code_postal",
                "ville",
                "url",
                "email",
                "location",
                "telephone",
                "nom_commercial",
                "siret",
                "identifiant_externe",
                "acteur_type_id",
                "statut",
                "source_id",
                "cree_le",
                "horaires_description",
                "modifie_le",
                "commentaires",
            ]
        ].to_sql(
            "qfdmo_acteur",
            connection,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

        df_labels[["acteur_id", "labelqualite_id"]].to_sql(
            "qfdmo_acteur_labels",
            connection,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

        df_pds[["id", "acteur_service_id", "action_id", "acteur_id"]].to_sql(
            "qfdmo_propositionservice",
            connection,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

        df_pdssc[["propositionservice_id", "souscategorieobjet_id"]].to_sql(
            "qfdmo_propositionservice_sous_categories",
            connection,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

        update_query = f"""
            UPDATE qfdmo_dagrun
            SET status = 'FINISHED'
            WHERE id = {dag_run_id}
            """
        connection.execute(update_query)


fetch_parse_task = PythonOperator(
    task_id="fetch_and_parse_data",
    python_callable=fetch_and_parse_data,
    provide_context=True,
    dag=dag,
)


def skip_processing(**kwargs):
    print("No records to validate. DAG run completes successfully.")


skip_processing_task = PythonOperator(
    task_id="skip_processing",
    python_callable=skip_processing,
    provide_context=True,
    dag=dag,
)

branch_task = BranchPythonOperator(
    task_id="branch_processing",
    python_callable=check_for_validation,
    provide_context=True,
    dag=dag,
)

write_to_postgres_task = PythonOperator(
    task_id="write_to_postgres",
    python_callable=write_data_to_postgres,
    provide_context=True,
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
