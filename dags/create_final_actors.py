from datetime import datetime, timedelta

import pandas as pd
import shortuuid
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from utils.db_tasks import read_data_from_postgres


def apply_corrections_acteur(**kwargs):

    df_acteur = kwargs["ti"].xcom_pull(task_ids="load_acteur")
    df_revisionacteur = kwargs["ti"].xcom_pull(task_ids="load_revisionacteur")

    revisionacteur_parent_ids = df_revisionacteur["parent_id"].unique()

    df_revisionacteur_parents = df_revisionacteur[
        df_revisionacteur["identifiant_unique"].isin(revisionacteur_parent_ids)
    ]

    df_acteur = df_acteur.set_index("identifiant_unique")
    df_revisionacteur = df_revisionacteur.set_index("identifiant_unique")
    # suppression du if et ajout de errors="ignore" pour éviter les erreurs
    df_revisionacteur = df_revisionacteur.drop(columns=["cree_le"], errors="ignore")
    df_acteur.update(df_revisionacteur)

    df_acteur_merged = pd.concat(
        [df_acteur, df_revisionacteur_parents.set_index("identifiant_unique")]
    ).reset_index()
    df_children = (
        df_revisionacteur.reset_index()
        .query("parent_id.notnull()")
        .drop_duplicates(subset=["parent_id", "identifiant_unique"])
    )
    df_children = pd.merge(
        df_children[["parent_id", "identifiant_unique"]],
        df_acteur_merged[["identifiant_unique", "source_id"]],
        on="identifiant_unique",
    )
    df_acteur_merged = df_acteur_merged[
        ~df_acteur_merged["identifiant_unique"].isin(
            df_children["identifiant_unique"].tolist()
        )
    ].copy()

    # Add a new column uuid to make the displayedacteur id without source name in id
    df_acteur_merged["uuid"] = df_acteur_merged["identifiant_unique"].apply(
        lambda x: shortuuid.uuid(name=x)
    )

    return {
        "df_acteur_merged": df_acteur_merged,
        # ["parent_id", "child_id", "child_source_id"]
        "df_children": df_children[
            ["parent_id", "identifiant_unique", "source_id"]
        ].reset_index(drop=True),
    }


def apply_corrections_propositionservices(**kwargs):
    df_propositionservice = kwargs["ti"].xcom_pull(task_ids="load_propositionservice")
    df_revisionpropositionservice = kwargs["ti"].xcom_pull(
        task_ids="load_revisionpropositionservice"
    )
    df_revisionpropositionservice = df_revisionpropositionservice.rename(
        columns={"revision_acteur_id": "acteur_id"}
    )
    df_propositionservice_sous_categories = kwargs["ti"].xcom_pull(
        task_ids="load_propositionservice_sous_categories"
    )
    df_revisionpropositionservice_sous_categories = kwargs["ti"].xcom_pull(
        task_ids="load_revisionpropositionservice_sous_categories"
    )
    df_revisionpropositionservice_sous_categories = (
        df_revisionpropositionservice_sous_categories.rename(
            columns={"revisionpropositionservice_id": "propositionservice_id"}
        )
    )
    df_revisionacteur = kwargs["ti"].xcom_pull(task_ids="load_revisionacteur")

    # Remove the propositionservice for the acteur that have a revision
    df_propositionservice = df_propositionservice[
        ~df_propositionservice["acteur_id"].isin(
            df_revisionacteur["identifiant_unique"]
        )
    ]

    df_propositionservice_merged = pd.concat(
        [
            # Remove the propositionservice for the acteur that have a revision
            df_propositionservice,
            df_revisionpropositionservice,
        ],
        ignore_index=True,
    )

    revisionpropositionservice_ids = df_revisionpropositionservice["id"].unique()
    propositionservice_ids = df_propositionservice["id"].unique()

    df_revisionpropositionservice_sous_categories = (
        df_revisionpropositionservice_sous_categories[
            df_revisionpropositionservice_sous_categories["propositionservice_id"].isin(
                revisionpropositionservice_ids
            )
        ]
    )
    df_propositionservice_sous_categories = df_propositionservice_sous_categories[
        df_propositionservice_sous_categories["propositionservice_id"].isin(
            propositionservice_ids
        )
    ]
    df_propositionservice_sous_categories_merged = pd.concat(
        [
            df_revisionpropositionservice_sous_categories,
            df_propositionservice_sous_categories,
        ],
        ignore_index=True,
    )

    return {
        "df_propositionservice_merged": df_propositionservice_merged,
        "df_propositionservice_sous_categories_merged": (
            df_propositionservice_sous_categories_merged
        ),
    }


def deduplicate_propositionservices(**kwargs):
    df_children = kwargs["ti"].xcom_pull(task_ids="apply_corrections_acteur")[
        "df_children"
    ]
    data_task_ps = kwargs["ti"].xcom_pull(
        task_ids="apply_corrections_propositionservices"
    )
    df_propositionservice_merged = data_task_ps["df_propositionservice_merged"]
    df_propositionservice_sous_categories_merged = data_task_ps[
        "df_propositionservice_sous_categories_merged"
    ]
    df_joined = df_propositionservice_merged.merge(
        df_children, left_on="acteur_id", right_on="identifiant_unique", how="inner"
    )
    df_joined_with_sous_categories = df_joined.merge(
        df_propositionservice_sous_categories_merged,
        left_on="id",
        right_on="propositionservice_id",
        how="inner",
    )

    df_grouped = (
        df_joined_with_sous_categories.groupby(["parent_id", "action_id"])
        .agg({"souscategorieobjet_id": lambda x: list(set(x))})
        .reset_index()
    )
    max_id = df_propositionservice_merged["id"].max()
    df_grouped["propositionservice_id"] = range(
        max_id + 1, max_id + 1 + len(df_grouped)
    )

    df_new_sous_categories = df_grouped.explode("souscategorieobjet_id")[
        ["propositionservice_id", "souscategorieobjet_id"]
    ]

    df_final_sous_categories = pd.concat(
        [df_propositionservice_sous_categories_merged, df_new_sous_categories],
        ignore_index=True,
    )

    df_final_ps_updated = pd.concat(
        [
            df_propositionservice_merged,
            df_grouped.rename(
                columns={"propositionservice_id": "id", "parent_id": "acteur_id"}
            )[["id", "action_id", "acteur_id"]],
        ],
        ignore_index=True,
    )

    children_ids = df_children["identifiant_unique"].unique()

    df_children_ps_ids = df_final_ps_updated[
        df_final_ps_updated["acteur_id"].isin(children_ids)
    ]["id"].unique()

    df_final_ps_updated = df_final_ps_updated[
        ~df_final_ps_updated["acteur_id"].isin(children_ids)
    ]

    df_final_sous_categories = df_final_sous_categories[
        ~df_final_sous_categories["propositionservice_id"].isin(df_children_ps_ids)
    ]

    return {
        "df_final_ps_updated": df_final_ps_updated,
        "df_final_sous_categories": df_final_sous_categories,
    }


def write_data_to_postgres(**kwargs):
    df_acteur_merged = kwargs["ti"].xcom_pull(task_ids="apply_corrections_acteur")[
        "df_acteur_merged"
    ]
    df_labels_updated = kwargs["ti"].xcom_pull(task_ids="deduplicate_labels")
    df_acteur_services_updated = kwargs["ti"].xcom_pull(
        task_ids="deduplicate_acteur_serivces"
    )
    df_acteur_sources_updated = kwargs["ti"].xcom_pull(
        task_ids="deduplicate_acteur_sources"
    )
    task_output = kwargs["ti"].xcom_pull(task_ids="deduplicate_propositionservices")

    df_propositionservice_merged = task_output["df_final_ps_updated"]
    df_propositionservice_sous_categories_merged = task_output[
        "df_final_sous_categories"
    ]
    df_propositionservice_sous_categories_merged.rename(
        columns={"propositionservice_id": "displayedpropositionservice_id"},
        inplace=True,
    )

    pg_hook = PostgresHook(postgres_conn_id="qfdmo-django-db")
    engine = pg_hook.get_sqlalchemy_engine()

    original_table_name_actor = "qfdmo_displayedacteur"
    temp_table_name_actor = "qfdmo_displayedacteurtemp"

    original_table_name_labels = "qfdmo_displayedacteur_labels"
    temp_table_name_labels = "qfdmo_displayedacteurtemp_labels"

    original_table_name_acteur_services = "qfdmo_displayedacteur_acteur_services"
    temp_table_name_acteur_services = "qfdmo_displayedacteurtemp_acteur_services"

    original_table_name_sources = "qfdmo_displayedacteur_sources"
    temp_table_name_sources = "qfdmo_displayedacteurtemp_sources"

    original_table_name_ps = "qfdmo_displayedpropositionservice"
    temp_table_name_ps = "qfdmo_displayedpropositionservicetemp"

    original_table_name_pssc = "qfdmo_displayedpropositionservice_sous_categories"
    temp_table_name_pssc = "qfdmo_displayedpropositionservicetemp_sous_categories"

    with engine.connect() as conn:
        conn.execute(f"DELETE FROM {temp_table_name_pssc}")
        conn.execute(f"DELETE FROM {temp_table_name_ps}")
        conn.execute(f"DELETE FROM {temp_table_name_labels}")
        conn.execute(f"DELETE FROM {temp_table_name_acteur_services}")
        conn.execute(f"DELETE FROM {temp_table_name_sources}")
        conn.execute(f"DELETE FROM {temp_table_name_actor}")

        df_acteur_merged[
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
                "uuid",
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

        df_acteur_sources_updated[["displayedacteur_id", "source_id"]].to_sql(
            temp_table_name_sources,
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

        df_propositionservice_merged[["id", "action_id", "acteur_id"]].to_sql(
            temp_table_name_ps,
            engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

        df_propositionservice_sous_categories_merged[
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
            f"ALTER TABLE {original_table_name_sources} "
            f"RENAME TO {original_table_name_sources}_old"
        )
        conn.execute(
            f"ALTER TABLE {temp_table_name_sources} "
            f"RENAME TO {original_table_name_sources}"
        )
        conn.execute(
            f"ALTER TABLE {original_table_name_sources}_old "
            f"RENAME TO {temp_table_name_sources}"
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
        "load_acteur_labels", "load_revisionacteur_labels", **kwargs
    )


# FIXME : This function should be tested
def merge_acteur_services(**kwargs):
    return _merge_acteurs_many2many_relationship(
        "load_acteur_acteur_services", "load_revisionacteur_acteur_services", **kwargs
    )


def deduplicate_labels(**kwargs):
    return _deduplicate_acteurs_many2many_relationship(
        "merge_labels", "labelqualite_id", **kwargs
    )


def deduplicate_acteur_serivces(**kwargs):
    return _deduplicate_acteurs_many2many_relationship(
        "merge_acteur_services", "acteurservice_id", **kwargs
    )


def deduplicate_acteur_sources(**kwargs):
    data_actors = kwargs["ti"].xcom_pull(task_ids="apply_corrections_acteur")
    df_children = data_actors["df_children"]
    df_acteur_merged = data_actors["df_acteur_merged"]

    df_acteur_sources_without_parents = df_acteur_merged[
        ~df_acteur_merged["identifiant_unique"].isin(df_children["parent_id"])
    ][["identifiant_unique", "source_id"]]

    df_acteur_sources_without_parents = df_acteur_sources_without_parents.rename(
        columns={"identifiant_unique": "displayedacteur_id"}
    )

    parents_df = df_children[["parent_id", "source_id"]].drop_duplicates()

    parents_df = parents_df.rename(columns={"parent_id": "displayedacteur_id"})

    result_df = pd.concat(
        [df_acteur_sources_without_parents, parents_df], ignore_index=True
    )

    result_df = result_df[
        ~result_df["displayedacteur_id"].isin(
            df_children["identifiant_unique"].tolist()
        )
    ]

    return result_df


def _merge_acteurs_many2many_relationship(
    link_with_acteur_task_id: str, link_with_revisionacteur_task_id: str, **kwargs: dict
):
    # Pull dataframes
    df_link_with_acteur = kwargs["ti"].xcom_pull(task_ids=link_with_acteur_task_id)
    df_link_with_revisionacteur = kwargs["ti"].xcom_pull(
        task_ids=link_with_revisionacteur_task_id
    )
    df_revisionacteur = kwargs["ti"].xcom_pull(task_ids="load_revisionacteur")

    # Remove the link_with_acteur for the acteur that have a revision
    df_link_with_acteur = df_link_with_acteur[
        ~df_link_with_acteur["acteur_id"].isin(df_revisionacteur["identifiant_unique"])
    ].copy()

    # Rename 'acteur_id' column to 'displayedacteur_id' and drop 'id' column
    df_link_with_acteur.rename(
        columns={"acteur_id": "displayedacteur_id"}, inplace=True
    )
    df_link_with_acteur.drop(columns=["id"], inplace=True)

    # Rename 'revisionacteur_id' column to 'displayedacteur_id' and drop 'id' column
    df_link_with_revisionacteur.rename(
        columns={"revisionacteur_id": "displayedacteur_id"}, inplace=True
    )
    df_link_with_revisionacteur.drop(columns=["id"], inplace=True)

    # Concatenate dataframes excluding common 'displayedacteur_id' in df_actor
    df_link_with_acteur_merged = pd.concat(
        [
            df_link_with_acteur,
            df_link_with_revisionacteur,
        ]
    ).drop_duplicates()

    return df_link_with_acteur_merged


def _deduplicate_acteurs_many2many_relationship(
    merged_relationship_task_id: str, col: str, **kwargs: dict
):
    df_children = kwargs["ti"].xcom_pull(task_ids="apply_corrections_acteur")[
        "df_children"
    ]
    df_merged_relationship = kwargs["ti"].xcom_pull(
        task_ids=merged_relationship_task_id
    )

    # Keep only the relationship of the children
    df_children_relationship = df_children.merge(
        df_merged_relationship,
        left_on="identifiant_unique",
        right_on="displayedacteur_id",
        how="inner",
    )

    # Deduplicate the relationship : renaming parent_id to displayedacteur_id
    df_children_relationship.drop(columns=["displayedacteur_id"], inplace=True)
    df_children_relationship.drop_duplicates(
        subset=["parent_id", col], keep="first", inplace=True
    )
    df_children_relationship.rename(
        columns={"parent_id": "displayedacteur_id"}, inplace=True
    )

    df_relationship = pd.concat(
        [df_merged_relationship, df_children_relationship[["displayedacteur_id", col]]],
        ignore_index=True,
    )
    df_relationship = df_relationship[
        ~df_relationship["displayedacteur_id"].isin(
            df_children["identifiant_unique"].tolist()
        )
    ]

    return df_relationship


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
    dag_id="compute_carte_acteur",
    dag_display_name="Rafraîchir les acteurs affichés sur la carte",
    default_args=default_args,
    description=(
        "Ce DAG récupère les données des acteurs et des propositions de services et"
        " applique les corrections. De plus, il déduplique les acteurs déclarés par"
        " plusieurs sources en cumulant leur services, sources et propositions"
        " services."
    ),
    schedule=None,
)

load_acteur_task = PythonOperator(
    task_id="load_acteur",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_acteur"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

load_propositionservice_task = PythonOperator(
    task_id="load_propositionservice",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_propositionservice"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

load_revisionacteur_task = PythonOperator(
    task_id="load_revisionacteur",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionacteur"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

load_revisionpropositionservice_task = PythonOperator(
    task_id="load_revisionpropositionservice",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionpropositionservice"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

load_revisionpropositionservice_sous_categories_task = PythonOperator(
    task_id="load_revisionpropositionservice_sous_categories",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionpropositionservice_sous_categories"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

load_propositionservice_sous_categories_task = PythonOperator(
    task_id="load_propositionservice_sous_categories",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_propositionservice_sous_categories"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

load_acteur_labels_task = PythonOperator(
    task_id="load_acteur_labels",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_acteur_labels"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

load_acteur_acteur_services_task = PythonOperator(
    task_id="load_acteur_acteur_services",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_acteur_acteur_services"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

read_revisionacteur_labels = PythonOperator(
    task_id="load_revisionacteur_labels",
    python_callable=read_data_from_postgres,
    op_kwargs={"table_name": "qfdmo_revisionacteur_labels"},
    dag=dag,
    retries=read_retry_count,
    retry_delay=read_retry_interval,
)

load_revisionacteur_acteur_services_task = PythonOperator(
    task_id="load_revisionacteur_acteur_services",
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

deduplicate_labels_task = PythonOperator(
    task_id="deduplicate_labels",
    python_callable=deduplicate_labels,
    dag=dag,
)

deduplicate_acteur_serivces_task = PythonOperator(
    task_id="deduplicate_acteur_serivces",
    python_callable=deduplicate_acteur_serivces,
    dag=dag,
)

deduplicate_acteur_sources_task = PythonOperator(
    task_id="deduplicate_acteur_sources",
    python_callable=deduplicate_acteur_sources,
    dag=dag,
)


apply_corrections_acteur_task = PythonOperator(
    task_id="apply_corrections_acteur",
    python_callable=apply_corrections_acteur,
    dag=dag,
)

apply_corrections_propositionservices_task = PythonOperator(
    task_id="apply_corrections_propositionservices",
    python_callable=apply_corrections_propositionservices,
    dag=dag,
)

deduplicate_propositionservices_task = PythonOperator(
    task_id="deduplicate_propositionservices",
    python_callable=deduplicate_propositionservices,
    dag=dag,
)


write_pos = PythonOperator(
    task_id="write_data_to_postgres",
    python_callable=write_data_to_postgres,
    dag=dag,
)

load_acteur_task >> apply_corrections_acteur_task
[
    load_propositionservice_task,
    load_revisionpropositionservice_task,
    load_propositionservice_sous_categories_task,
    load_revisionpropositionservice_sous_categories_task,
] >> apply_corrections_propositionservices_task
[
    load_revisionacteur_task,
    load_acteur_labels_task,
    read_revisionacteur_labels,
] >> merge_labels_task
[
    load_revisionacteur_task,
    load_acteur_acteur_services_task,
    load_revisionacteur_acteur_services_task,
] >> merge_acteur_services_task
apply_corrections_acteur_task >> deduplicate_propositionservices_task
apply_corrections_acteur_task >> deduplicate_acteur_sources_task
apply_corrections_propositionservices_task >> deduplicate_propositionservices_task
merge_labels_task >> apply_corrections_acteur_task >> deduplicate_labels_task
(
    merge_acteur_services_task
    >> apply_corrections_acteur_task
    >> deduplicate_acteur_serivces_task
)
deduplicate_acteur_sources_task >> write_pos
deduplicate_propositionservices_task >> write_pos
deduplicate_labels_task >> write_pos
deduplicate_acteur_serivces_task >> write_pos
