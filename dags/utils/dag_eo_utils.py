import json
import logging
from datetime import datetime
from typing import Union

import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook
from utils import logging_utils as log
from utils import shared_constants as constants

logger = logging.getLogger(__name__)


def db_data_prepare(**kwargs):
    # Removed acteurs
    df_acteur_to_delete = kwargs["ti"].xcom_pull(task_ids="propose_acteur_to_delete")[
        "df_acteur_to_delete"
    ]
    update_actors_columns = ["identifiant_unique", "statut", "cree_le"]
    df_acteur_to_delete["row_updates"] = df_acteur_to_delete[
        update_actors_columns
    ].apply(lambda row: json.dumps(row.to_dict(), default=str), axis=1)
    # Created or updated Acteurs
    df_actors = kwargs["ti"].xcom_pull(task_ids="propose_acteur_changes")["df"]
    df_ps = kwargs["ti"].xcom_pull(task_ids="propose_services")["df"]
    df_pssc = kwargs["ti"].xcom_pull(task_ids="propose_services_sous_categories")
    df_labels = kwargs["ti"].xcom_pull(task_ids="propose_labels")
    df_acteur_services = kwargs["ti"].xcom_pull(task_ids="propose_acteur_services")
    df_acteur_services = (
        df_acteur_services
        if df_acteur_services is not None
        else pd.DataFrame(columns=["acteur_id", "acteurservice_id"])
    )

    log.preview("df_acteur_to_delete", df_acteur_to_delete)
    log.preview("df_actors", df_actors)
    log.preview("df_ps", df_ps)
    log.preview("df_pssc", df_pssc)
    log.preview("df_labels", df_labels)
    log.preview("df_acteur_services", df_acteur_services)

    if df_actors.empty:
        raise ValueError("df_actors est vide")
    if df_ps.empty:
        raise ValueError("df_ps est vide")
    if df_pssc.empty:
        raise ValueError("df_pssc est vide")

    aggregated_pdsc = (
        df_pssc.groupby("propositionservice_id")
        .apply(lambda x: x.to_dict("records") if not x.empty else [])
        .reset_index(name="pds_sous_categories")
    )

    df_pds_joined = pd.merge(
        df_ps,
        aggregated_pdsc,
        how="left",
        left_on="id",
        right_on="propositionservice_id",
    )
    df_pds_joined["propositionservice_id"] = df_pds_joined[
        "propositionservice_id"
    ].astype(str)

    df_pds_joined["pds_sous_categories"] = df_pds_joined["pds_sous_categories"].apply(
        lambda x: x if isinstance(x, list) else []
    )

    df_pds_joined.drop("id", axis=1, inplace=True)

    aggregated_pds = (
        df_pds_joined.groupby("acteur_id")
        .apply(lambda x: x.to_dict("records") if not x.empty else [])
        .reset_index(name="proposition_services")
    )

    aggregated_labels = df_labels.groupby("acteur_id").apply(
        lambda x: x.to_dict("records") if not x.empty else []
    )
    aggregated_labels = (
        pd.DataFrame(columns=["acteur_id", "labels"])
        if aggregated_labels.empty
        else aggregated_labels.reset_index(name="labels")
    )

    aggregated_acteur_services = df_acteur_services.groupby("acteur_id").apply(
        lambda x: x.to_dict("records") if not x.empty else []
    )
    aggregated_acteur_services = (
        pd.DataFrame(columns=["acteur_id", "acteur_services"])
        if aggregated_acteur_services.empty
        else aggregated_acteur_services.reset_index(name="acteur_services")
    )

    df_joined_with_pds = pd.merge(
        df_actors,
        aggregated_pds,
        how="left",
        left_on="identifiant_unique",
        right_on="acteur_id",
    )

    df_joined_with_labels = pd.merge(
        df_joined_with_pds,
        aggregated_labels,
        how="left",
        left_on="acteur_id",
        right_on="acteur_id",
    )

    df_joined = pd.merge(
        df_joined_with_labels,
        aggregated_acteur_services,
        how="left",
        left_on="acteur_id",
        right_on="acteur_id",
    )

    df_joined["proposition_services"] = df_joined["proposition_services"].apply(
        lambda x: x if isinstance(x, list) else []
    )

    df_joined.loc[
        df_joined["proposition_services"].apply(lambda x: x == []), "status"
    ] = "SUPPRIME"

    df_joined.drop("acteur_id", axis=1, inplace=True)

    df_joined = df_joined.where(pd.notna(df_joined), None)

    df_joined["row_updates"] = df_joined.apply(
        lambda row: json.dumps(row.to_dict(), default=str), axis=1
    )
    df_joined.drop_duplicates("identifiant_unique", keep="first", inplace=True)
    log.preview("df_joined", df_joined)
    log.preview("df_acteur_to_delete", df_acteur_to_delete)

    return {"all": {"df": df_joined}, "to_disable": {"df": df_acteur_to_delete}}


def insert_dagrun_and_process_df(df_acteur_updates, metadata, dag_name, run_name):
    if df_acteur_updates.empty:
        return
    pg_hook = PostgresHook(postgres_conn_id="qfdmo_django_db")
    engine = pg_hook.get_sqlalchemy_engine()
    current_date = datetime.now()

    with engine.connect() as conn:
        # Insert a new dagrun
        result = conn.execute(
            """
            INSERT INTO qfdmo_dagrun
            (dag_id, run_id, status, meta_data, created_date, updated_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING ID;
        """,
            (
                dag_name,
                run_name,
                "TO_VALIDATE",
                json.dumps(metadata),
                current_date,
                current_date,
            ),
        )
        dag_run_id = result.fetchone()[0]

    # Insert dag_run_change
    df_acteur_updates["change_type"] = df_acteur_updates["event"]
    df_acteur_updates["dag_run_id"] = dag_run_id
    df_acteur_updates["status"] = constants.TO_VALIDATE
    df_acteur_updates[["row_updates", "dag_run_id", "change_type", "status"]].to_sql(
        "qfdmo_dagrunchange",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )


def write_to_dagruns(**kwargs):
    dag_name = kwargs["dag"].dag_display_name or kwargs["dag"].dag_id
    run_id = kwargs["run_id"]
    dfs = kwargs["ti"].xcom_pull(task_ids="db_data_prepare")
    metadata_actors = (
        kwargs["ti"]
        .xcom_pull(task_ids="propose_acteur_changes", key="return_value", default={})
        .get("metadata", {})
    )
    metadata_acteur_to_delete = (
        kwargs["ti"]
        .xcom_pull(task_ids="propose_acteur_to_delete", key="return_value", default={})
        .get("metadata", {})
    )
    metadata_pds = (
        kwargs["ti"]
        .xcom_pull(task_ids="propose_services", key="return_value", default={})
        .get("metadata", {})
    )

    metadata = {**metadata_actors, **metadata_acteur_to_delete, **metadata_pds}

    for key, data in dfs.items():
        # TODO dag_id
        dag_name_suffixed = (
            dag_name if key == "all" else f"{dag_name} - {key.replace('_', ' ')}"
        )
        run_name = run_id.replace("__", " - ")
        df = data["df"]
        metadata.update(data.get("metadata", {}))
        insert_dagrun_and_process_df(df, metadata, dag_name_suffixed, run_name)


def mapping_try_or_fallback_column_value(
    df_column: pd.Series,
    values_mapping: dict,
    default_value: Union[str, bool, None] = None,
) -> pd.Series:
    # set to default value if column is not one of keys or values in values_mapping
    return (
        df_column.str.strip()
        .str.lower()
        .replace(values_mapping)
        .apply(lambda x: (default_value if x not in values_mapping.values() else x))
    )


def cast_eo_boolean_or_string_to_boolean(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower().strip() == "oui"
    return False


def merge_produits_accepter(group):
    produits_sets = set()
    for produits in group:
        produits_sets.update([produit.strip() for produit in produits.split("|")])
    return "|".join(sorted(produits_sets))


def merge_duplicates(
    df, group_column="identifiant_unique", merge_column="produitsdechets_acceptes"
):

    df_duplicates = df[df.duplicated(group_column, keep=False)]
    df_non_duplicates = df[~df.duplicated(group_column, keep=False)]

    df_merged_duplicates = (
        df_duplicates.groupby(group_column)
        .agg(
            {
                **{
                    col: "first"
                    for col in df.columns
                    if col != merge_column and col != group_column
                },
                merge_column: merge_produits_accepter,
            }
        )
        .reset_index()
    )

    # Concatenate the non-duplicates and merged duplicates
    df_final = pd.concat([df_non_duplicates, df_merged_duplicates], ignore_index=True)

    return df_final
