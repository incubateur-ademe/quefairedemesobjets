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

    unique_parent_ids = df_manual_actor_updates["parent_id"].unique()

    df_new_parents = df_manual_actor_updates[
        df_manual_actor_updates["identifiant_unique"].isin(unique_parent_ids)
    ]

    df_normalized_actors = df_normalized_actors.set_index("identifiant_unique")
    df_manual_actor_updates = df_manual_actor_updates.set_index("identifiant_unique")
    if "cree_le" in df_manual_actor_updates.columns:
        df_manual_actor_updates = df_manual_actor_updates.drop(columns=["cree_le"])
    df_normalized_actors.update(df_manual_actor_updates)
    df_normalized_actors = pd.concat(
        [df_normalized_actors, df_new_parents.set_index("identifiant_unique")]
    )

    parents = (
        df_manual_actor_updates.reset_index()
        .query("parent_id.notnull()")
        .drop_duplicates(subset=["parent_id", "identifiant_unique"])
        .rename(columns={"identifiant_unique": "child_id"})
    )

    return {
        "df_normalized_actors": df_normalized_actors.reset_index(),
        "parents": parents[["parent_id", "child_id"]].reset_index(drop=True),
    }


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


def deduplicate_proposition_services_and_sous_categories(**kwargs):
    df_parents = kwargs["ti"].xcom_pull(task_ids="apply_corrections_actors")["parents"]
    data_task_ps = kwargs["ti"].xcom_pull(
        task_ids="apply_corrections_propositionservice"
    )
    df_ps_updated = data_task_ps["df_ps_updated"]
    df_sous_categories_updated = data_task_ps["df_sous_categories_updated"]
    df_joined = df_ps_updated.merge(
        df_parents, left_on="acteur_id", right_on="child_id", how="inner"
    )
    df_joined_with_sous_categories = df_joined.merge(
        df_sous_categories_updated,
        left_on="id",
        right_on="propositionservice_id",
        how="inner",
    )

    df_grouped = (
        df_joined_with_sous_categories.groupby(["parent_id", "action_id"])
        .agg({"souscategorieobjet_id": lambda x: list(set(x))})
        .reset_index()
    )
    max_id = df_ps_updated["id"].max()
    df_grouped["propositionservice_id"] = range(
        max_id + 1, max_id + 1 + len(df_grouped)
    )

    df_new_sous_categories = df_grouped.explode("souscategorieobjet_id")[
        ["propositionservice_id", "souscategorieobjet_id"]
    ]

    df_final_sous_categories = pd.concat(
        [df_sous_categories_updated, df_new_sous_categories], ignore_index=True
    )

    df_final_ps_updated = pd.concat(
        [
            df_ps_updated,
            df_grouped.rename(
                columns={"propositionservice_id": "id", "parent_id": "acteur_id"}
            )[["id", "action_id", "acteur_id"]],
        ],
        ignore_index=True,
    )

    return {
        "df_final_ps_updated": df_final_ps_updated,
        "df_final_sous_categories": df_final_sous_categories,
    }


def write_data_to_postgres(**kwargs):
    df_normalized_corrected_actors = kwargs["ti"].xcom_pull(
        task_ids="apply_corrections_actors"
    )["df_normalized_actors"]
    df_labels_updated = kwargs["ti"].xcom_pull(task_ids="dedup_labels")
    df_acteur_services_updated = kwargs["ti"].xcom_pull(
        task_ids="dedup_acteur_services"
    )
    task_output = kwargs["ti"].xcom_pull(task_ids="apply_dedup_propositionservice")

    df_ps_updated = task_output["df_final_ps_updated"]
    df_sous_categories_updated = task_output["df_final_sous_categories"]
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

    original_table_name_acteur_services = "qfdmo_displayedacteur_acteur_services"
    temp_table_name_acteur_services = "qfdmo_displayedacteurtemp_acteur_services"

    original_table_name_ps = "qfdmo_displayedpropositionservice"
    temp_table_name_ps = "qfdmo_displayedpropositionservicetemp"

    original_table_name_pssc = "qfdmo_displayedpropositionservice_sous_categories"
    temp_table_name_pssc = "qfdmo_displayedpropositionservicetemp_sous_categories"

    with engine.connect() as conn:
        conn.execute(f"DELETE FROM {temp_table_name_pssc}")
        conn.execute(f"DELETE FROM {temp_table_name_ps}")
        conn.execute(f"DELETE FROM {temp_table_name_labels}")
        conn.execute(f"DELETE FROM {temp_table_name_acteur_services}")
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
                "public_accueilli",
                "reprise",
                "exclusivite_de_reprisereparation",
                "uniquement_sur_rdv",
                "action_principale_id",
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

        df_acteur_services_updated[["displayedacteur_id", "acteurservice_id"]].to_sql(
            temp_table_name_acteur_services,
            engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

        df_ps_updated[["id", "action_id", "acteur_id"]].to_sql(
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
            f"ALTER TABLE {original_table_name_acteur_services} "
            f"RENAME TO {original_table_name_acteur_services}_old"
        )
        conn.execute(
            f"ALTER TABLE {temp_table_name_acteur_services} "
            f"RENAME TO {original_table_name_acteur_services}"
        )
        conn.execute(
            f"ALTER TABLE {original_table_name_acteur_services}_old "
            f"RENAME TO {temp_table_name_acteur_services}"
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


def merge_labels(**kwargs):
    return _merge_acteurs_many2many_relationship(
        "read_acteur_labels", "read_revisionacteur_labels", **kwargs
    )


# FIXME : This function should be tested
def merge_acteur_services(**kwargs):
    return _merge_acteurs_many2many_relationship(
        "read_acteur_acteur_services", "read_revisionacteur_acteur_services", **kwargs
    )


def deduplicate_labels(**kwargs):
    return _deduplicate_acteurs_many2many_relationship(
        "merge_labels", "labelqualite_id", **kwargs
    )


def deduplicate_acteur_serivces(**kwargs):
    return _deduplicate_acteurs_many2many_relationship(
        "merge_acteur_services", "acteurservice_id", **kwargs
    )


def _merge_acteurs_many2many_relationship(
    acteur_task_id: str, revisionacteur_task_id: str, **kwargs: dict
):
    # Pull dataframes
    df_acteur = kwargs["ti"].xcom_pull(task_ids=acteur_task_id)
    df_acteurrevision = kwargs["ti"].xcom_pull(task_ids=revisionacteur_task_id)

    # Rename 'acteur_id' column to 'displayedacteur_id' and drop 'id' column
    df_acteur.rename(columns={"acteur_id": "displayedacteur_id"}, inplace=True)
    df_acteur.drop(columns=["id"], inplace=True)

    # Rename 'revisionacteur_id' column to 'displayedacteur_id' and drop 'id' column
    df_acteurrevision.rename(
        columns={"revisionacteur_id": "displayedacteur_id"}, inplace=True
    )
    df_acteurrevision.drop(columns=["id"], inplace=True)

    # Get common 'displayedacteur_id'
    common_acteur_ids = df_acteur[
        df_acteur["displayedacteur_id"].isin(df_acteurrevision["displayedacteur_id"])
    ]["displayedacteur_id"].unique()

    # Concatenate dataframes excluding common 'displayedacteur_id' in df_actor
    df_merged = pd.concat(
        [
            df_acteur[~df_acteur["displayedacteur_id"].isin(common_acteur_ids)],
            df_acteurrevision,
        ]
    ).drop_duplicates()

    return df_merged


def _deduplicate_acteurs_many2many_relationship(
    merged_acteur_task_id: str, col: str, **kwargs: dict
):
    df_parents = kwargs["ti"].xcom_pull(task_ids="apply_corrections_actors")["parents"]
    merged_acteur = kwargs["ti"].xcom_pull(task_ids=merged_acteur_task_id)
    merged_df = df_parents.merge(
        merged_acteur, left_on="child_id", right_on="displayedacteur_id", how="inner"
    )
    merged_df = merged_df.drop(columns=["displayedacteur_id"])

    deduped_df = merged_df.drop_duplicates(subset=["parent_id", col], keep="first")

    deduped_df.rename(columns={"parent_id": "displayedacteur_id"}, inplace=True)
    final_df = pd.concat(
        [merged_acteur, deduped_df[["displayedacteur_id", col]]], ignore_index=True
    )

    return final_df


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 2, 7),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Retry settings for reading tasks
read_retry_count = 5
read_retry_interval = timedelta(minutes=2)

dag = DAG(
    utils.get_dag_name(__file__, "apply_adresse_corrections"),
    default_args=default_args,
    description=(
        "DAG for applying correction on normalized actors and propositionservice"
    ),
    schedule=None,
)

read_actors = PythonOperator(
    task_id="load_actors",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_acteur"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

read_ps = PythonOperator(
    task_id="load_propositionservice",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_propositionservice"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

read_revision_actor = PythonOperator(
    task_id="load_revision_actors",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionacteur"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

read_revision_ps = PythonOperator(
    task_id="load_revision_propositionservice",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionpropositionservice"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

read_revision_sc = PythonOperator(
    task_id="load_revision_ps_sous_categories",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionpropositionservice_sous_categories"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

read_sc = PythonOperator(
    task_id="load_ps_sous_categories",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_propositionservice_sous_categories"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

read_acteur_labels = PythonOperator(
    task_id="read_acteur_labels",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_acteur_labels"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

read_acteur_acteur_services = PythonOperator(
    task_id="read_acteur_acteur_services",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_acteur_acteur_services"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

read_revisionacteur_labels = PythonOperator(
    task_id="read_revisionacteur_labels",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionacteur_labels"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

read_revisionacteur_acteur_services = PythonOperator(
    task_id="read_revisionacteur_acteur_services",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionacteur_acteur_services"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)
# qfdmo_revisionacteur_acteur_services

merge_labels_task = PythonOperator(
    task_id="merge_labels",
    python_callable=merge_labels,
    dag=dag,
)

merge_acteur_services_task = PythonOperator(
    task_id="merge_acteur_services",
    python_callable=merge_acteur_services,
    dag=dag,
)

dedup_labels_task = PythonOperator(
    task_id="dedup_labels",
    python_callable=deduplicate_labels,
    dag=dag,
)

dedup_acteur_services_task = PythonOperator(
    task_id="dedup_acteur_services",
    python_callable=deduplicate_acteur_serivces,
    dag=dag,
)

apply_corr = PythonOperator(
    task_id="apply_corrections_actors",
    python_callable=apply_corrections,
    dag=dag,
)

apply_corr_ps = PythonOperator(
    task_id="apply_corrections_propositionservice",
    python_callable=apply_corrections_ps,
    dag=dag,
)

dedup_ps = PythonOperator(
    task_id="apply_dedup_propositionservice",
    python_callable=deduplicate_proposition_services_and_sous_categories,
    dag=dag,
)


write_pos = PythonOperator(
    task_id="write_data_to_postgres",
    python_callable=write_data_to_postgres,
    dag=dag,
)

[read_actors, read_revision_actor] >> apply_corr
[read_ps, read_revision_ps, read_sc, read_revision_sc] >> apply_corr_ps
[read_acteur_labels, read_revisionacteur_labels] >> merge_labels_task
[
    read_acteur_acteur_services,
    read_revisionacteur_acteur_services,
] >> merge_acteur_services_task
apply_corr >> dedup_ps
apply_corr_ps >> dedup_ps
merge_labels_task >> apply_corr >> dedup_labels_task
merge_acteur_services_task >> apply_corr >> dedup_acteur_services_task

dedup_ps >> write_pos
dedup_labels_task >> write_pos
dedup_acteur_services_task >> write_pos
