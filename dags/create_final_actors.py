from datetime import datetime, timedelta
from importlib import import_module
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

env = Path(__file__).parent.name
utils = import_module(f"{env}.utils.utils")


def read_data_from_postgres(**kwargs):
    table_name = kwargs["table_name"]
    pg_hook = PostgresHook(postgres_conn_id=utils.get_db_conn_id(__file__))
    engine = pg_hook.get_sqlalchemy_engine()
    df = utils.load_table(table_name, engine)
    return df


def apply_corrections(**kwargs):
    df_normalized_actors = kwargs["ti"].xcom_pull(task_ids="load_actors")
    df_manual_actor_updates = kwargs["ti"].xcom_pull(task_ids="load_revision_actors")

    df_normalized_actors = df_normalized_actors.set_index("identifiant_unique")
    df_manual_actor_updates = df_manual_actor_updates.set_index("identifiant_unique")

    df_normalized_actors.update(df_manual_actor_updates)

    return df_normalized_actors.reset_index()


def apply_corrections_ps(**kwargs):
    df_propositionservice = kwargs["ti"].xcom_pull(task_ids="load_propositionservice")
    df_manual_propositionservice_updates = kwargs["ti"].xcom_pull(
        task_ids="load_revision_propositionservice"
    )
    df_manual_propositionservice_updates = df_manual_propositionservice_updates.rename(
        columns={"revision_acteur_id": "acteur_id"}
    )
    df_ps_sous_categories = kwargs["ti"].xcom_pull(task_ids="load_ps_sous_categories")
    df_manual_propositionservice_sous_categories_updates = kwargs["ti"].xcom_pull(
        task_ids="load_revision_ps_sous_categories"
    )
    df_manual_propositionservice_sous_categories_updates = (
        df_manual_propositionservice_sous_categories_updates.rename(
            columns={"revisionpropositionservice_id": "propositionservice_id"}
        )
    )

    common_acteur_ids = df_propositionservice[
        df_propositionservice["acteur_id"].isin(
            df_manual_propositionservice_updates["acteur_id"]
        )
    ]["acteur_id"].unique()

    df_ps_updated = pd.concat(
        [
            df_propositionservice[
                ~df_propositionservice["acteur_id"].isin(common_acteur_ids)
            ],
            df_manual_propositionservice_updates,
        ],
        ignore_index=True,
    )
    rps_ids = df_manual_propositionservice_updates["id"].unique()
    only_ps_ids = df_propositionservice[
        ~df_propositionservice["acteur_id"].isin(common_acteur_ids)
    ]["id"].unique()

    matching_rpssc_rows = df_manual_propositionservice_sous_categories_updates[
        df_manual_propositionservice_sous_categories_updates[
            "propositionservice_id"
        ].isin(rps_ids)
    ]
    matching_pssc_rows = df_ps_sous_categories[
        df_ps_sous_categories["propositionservice_id"].isin(only_ps_ids)
    ]
    df_sous_categories_updated = pd.concat(
        [matching_rpssc_rows, matching_pssc_rows], ignore_index=True
    )

    return {
        "df_ps_updated": df_ps_updated,
        "df_sous_categories_updated": df_sous_categories_updated,
    }


def write_data_to_postgres(**kwargs):
    df_normalized_corrected_actors = kwargs["ti"].xcom_pull(
        task_ids="apply_corrections_actors"
    )
    df_labels_updated = kwargs["ti"].xcom_pull(task_ids="merge_labels")
    task_output = kwargs["ti"].xcom_pull(
        task_ids="apply_corrections_propositionservice"
    )
    df_ps_updated = task_output["df_ps_updated"]
    df_sous_categories_updated = task_output["df_sous_categories_updated"]
    df_sous_categories_updated.rename(
        columns={"propositionservice_id": "displayedpropositionservice_id"},
        inplace=True,
    )

    pg_hook = PostgresHook(postgres_conn_id=utils.get_db_conn_id(__file__))
    engine = pg_hook.get_sqlalchemy_engine()

    original_table_name_actor = "qfdmo_displayedacteur"
    temp_table_name_actor = "qfdmo_displayedacteurtemp"

    original_table_name_labels = "qfdmo_displayedacteur_labels"
    temp_table_name_labels = "qfdmo_displayedacteurtemp_labels"

    original_table_name_ps = "qfdmo_displayedpropositionservice"
    temp_table_name_ps = "qfdmo_displayedpropositionservicetemp"

    original_table_name_pssc = "qfdmo_displayedpropositionservice_sous_categories"
    temp_table_name_pssc = "qfdmo_displayedpropositionservicetemp_sous_categories"

    with engine.connect() as conn:
        conn.execute(f"DELETE FROM {temp_table_name_pssc}")
        conn.execute(f"DELETE FROM {temp_table_name_ps}")
        conn.execute(f"DELETE FROM {temp_table_name_labels}")
        conn.execute(f"DELETE FROM {temp_table_name_actor}")

        df_normalized_corrected_actors[
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
                "nom_officiel",
                "siret",
                "identifiant_externe",
                "acteur_type_id",
                "statut",
                "source_id",
                "cree_le",
                "modifie_le",
                "naf_principal",
                "commentaires",
                "horaires_osm",
                "horaires_description",
                "description",
            ]
        ].to_sql(
            temp_table_name_actor,
            engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )
        df_labels_updated[["displayedacteur_id", "labelqualite_id"]].to_sql(
            temp_table_name_labels,
            engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

        df_ps_updated[["id", "acteur_service_id", "action_id", "acteur_id"]].to_sql(
            temp_table_name_ps,
            engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

        df_sous_categories_updated[
            ["displayedpropositionservice_id", "souscategorieobjet_id"]
        ].to_sql(
            temp_table_name_pssc,
            engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

    with engine.begin() as conn:
        conn.execute(
            f"ALTER TABLE {original_table_name_actor} "
            f"RENAME TO {original_table_name_actor}_old"
        )
        conn.execute(
            f"ALTER TABLE {temp_table_name_actor} "
            f"RENAME TO {original_table_name_actor}"
        )
        conn.execute(
            f"ALTER TABLE {original_table_name_actor}_old "
            f"RENAME TO {temp_table_name_actor}"
        )

        conn.execute(
            f"ALTER TABLE {original_table_name_labels} "
            f"RENAME TO {original_table_name_labels}_old"
        )
        conn.execute(
            f"ALTER TABLE {temp_table_name_labels} "
            f"RENAME TO {original_table_name_labels}"
        )
        conn.execute(
            f"ALTER TABLE {original_table_name_labels}_old "
            f"RENAME TO {temp_table_name_labels}"
        )

        conn.execute(
            f"ALTER TABLE {original_table_name_ps} "
            f"RENAME TO {original_table_name_ps}_old"
        )
        conn.execute(
            f"ALTER TABLE {temp_table_name_ps} " f"RENAME TO {original_table_name_ps}"
        )
        conn.execute(
            f"ALTER TABLE {original_table_name_ps}_old "
            f"RENAME TO {temp_table_name_ps}"
        )

        conn.execute(
            f"ALTER TABLE {original_table_name_pssc} "
            f"RENAME TO {original_table_name_pssc}_old"
        )
        conn.execute(
            f"ALTER TABLE {temp_table_name_pssc} "
            f"RENAME TO {original_table_name_pssc}"
        )
        conn.execute(
            f"ALTER TABLE {original_table_name_pssc}_old "
            f"RENAME TO {temp_table_name_pssc}"
        )

    print("Table swap completed successfully.")


def merge_actors_labels(**kwargs):
    # Pull dataframes
    df_actor_labels = kwargs["ti"].xcom_pull(task_ids="load_actor_labels")
    df_revision_labels = kwargs["ti"].xcom_pull(task_ids="load_revision_labels")

    # Rename 'acteur_id' column to 'displayedacteur_id' and drop 'id' column
    df_actor_labels.rename(columns={"acteur_id": "displayedacteur_id"}, inplace=True)
    df_actor_labels.drop(columns=["id"], inplace=True)

    # Rename 'revisionacteur_id' column to 'displayedacteur_id' and drop 'id' column
    df_revision_labels.rename(
        columns={"revisionacteur_id": "displayedacteur_id"}, inplace=True
    )
    df_revision_labels.drop(columns=["id"], inplace=True)

    # Get common 'displayedacteur_id'
    common_acteur_ids = df_actor_labels[
        df_actor_labels["displayedacteur_id"].isin(
            df_revision_labels["displayedacteur_id"]
        )
    ]["displayedacteur_id"].unique()

    # Concatenate dataframes excluding common 'displayedacteur_id' in df_actor_labels
    df_merged_labels = pd.concat(
        [
            df_actor_labels[
                ~df_actor_labels["displayedacteur_id"].isin(common_acteur_ids)
            ],
            df_revision_labels,
        ]
    ).drop_duplicates()

    return df_merged_labels


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 2, 7),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    utils.get_dag_name(__file__, "apply_adresse_corrections"),
    default_args=default_args,
    description=(
        "DAG for applying correction on normalized actors and propositionservice"
    ),
    schedule_interval=None,
)

read_actors = PythonOperator(
    task_id="load_actors",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_acteur"},
    dag=dag,
)

read_ps = PythonOperator(
    task_id="load_propositionservice",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_propositionservice"},
    dag=dag,
)

read_revision_actor = PythonOperator(
    task_id="load_revision_actors",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionacteur"},
    dag=dag,
)

read_revision_ps = PythonOperator(
    task_id="load_revision_propositionservice",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionpropositionservice"},
    dag=dag,
)

read_revision_sc = PythonOperator(
    task_id="load_revision_ps_sous_categories",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionpropositionservice_sous_categories"},
    dag=dag,
)

read_sc = PythonOperator(
    task_id="load_ps_sous_categories",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_propositionservice_sous_categories"},
    dag=dag,
)

read_actor_labels = PythonOperator(
    task_id="load_actor_labels",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_acteur_labels"},
    dag=dag,
)

read_revision_labels = PythonOperator(
    task_id="load_revision_labels",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionacteur_labels"},
    dag=dag,
)

merge_labels = PythonOperator(
    task_id="merge_labels",
    python_callable=merge_actors_labels,
    provide_context=True,
    dag=dag,
)

apply_corr = PythonOperator(
    task_id="apply_corrections_actors",
    python_callable=apply_corrections,
    provide_context=True,
    dag=dag,
)

apply_corr_ps = PythonOperator(
    task_id="apply_corrections_propositionservice",
    python_callable=apply_corrections_ps,
    provide_context=True,
    dag=dag,
)

write_pos = PythonOperator(
    task_id="write_data_to_postgres",
    python_callable=write_data_to_postgres,
    provide_context=True,
    dag=dag,
)

[read_actors, read_revision_actor] >> apply_corr
[read_ps, read_revision_ps, read_sc, read_revision_sc] >> apply_corr_ps
[read_actor_labels, read_revision_labels] >> merge_labels
[merge_labels, apply_corr, apply_corr_ps] >> write_pos
