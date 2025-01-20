import logging

import pandas as pd
from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from sources.config import shared_constants as constants
from suggestions.tasks.business_logic.db_read_suggestiontoprocess import (
    get_first_suggetsioncohorte_to_insert,
)
from utils import logging_utils as log


def db_normalize_suggestion():
    suggestion_cohorte = get_first_suggetsioncohorte_to_insert()
    if suggestion_cohorte is None:
        raise ValueError("No suggestion found")
    suggestion_cohorte_id = suggestion_cohorte["id"]
    type_action = suggestion_cohorte["type_action"]
    logging.warning(f"Processing suggestion_cohorte_id: {suggestion_cohorte_id}")
    logging.warning(f"Processing suggestion_cohorte: {suggestion_cohorte}")
    logging.warning(
        f"Processing suggestion_cohorte: {suggestion_cohorte['type_action']}"
    )

    engine = PostgresConnectionManager().engine

    df_sql = pd.read_sql_query(
        f"""
        SELECT * FROM data_suggestion
        WHERE suggestion_cohorte_id = '{suggestion_cohorte_id}'
        """,
        engine,
    )
    log.preview("df_acteur_to_delete", df_sql)

    if (
        type_action
        in [
            constants.SUGGESTION_SOURCE_AJOUT,
            constants.SUGGESTION_SOURCE_MISESAJOUR,
        ]
        and not df_sql.empty
    ):
        normalized_dfs = df_sql["suggestion"].apply(pd.json_normalize)
        df_acteur = pd.concat(normalized_dfs.tolist(), ignore_index=True)
        return normalize_acteur_update_for_db(
            df_acteur, suggestion_cohorte_id, engine, type_action
        )
    if type_action == constants.SUGGESTION_SOURCE_SUPRESSION and not df_sql.empty:
        normalized_dfs = df_sql["suggestion"].apply(pd.json_normalize)
        df_acteur = pd.concat(normalized_dfs.tolist(), ignore_index=True)
        log.preview("df_acteur_to_delete", df_acteur)
        return {
            "actors": df_acteur,
            "dag_run_id": suggestion_cohorte_id,
            "change_type": type_action,
        }

    raise ValueError("No suggestion found")


def normalize_acteur_update_for_db(df_actors, dag_run_id, engine, type_action):
    df_labels = process_many2many_df(df_actors, "labels")
    df_acteur_services = process_many2many_df(
        df_actors, "acteur_services", df_columns=["acteur_id", "acteurservice_id"]
    )

    max_id_pds = pd.read_sql_query(
        "SELECT max(id) FROM qfdmo_propositionservice", engine
    )["max"][0]
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
        "pds": df_pds[["id", "action_id", "acteur_id"]],
        "pds_sous_categories": df_pdssc[
            ["propositionservice_id", "souscategorieobjet_id"]
        ],
        "dag_run_id": dag_run_id,
        "labels": df_labels[["acteur_id", "labelqualite_id"]],
        "acteur_services": df_acteur_services[["acteur_id", "acteurservice_id"]],
        "change_type": type_action,
    }


def process_many2many_df(df, column_name, df_columns=["acteur_id", "labelqualite_id"]):
    try:
        # Attempt to process the 'labels' column if it exists and is not empty
        normalized_df = df[column_name].dropna().apply(pd.json_normalize)
        if normalized_df.empty:
            return pd.DataFrame(
                columns=df_columns
            )  # Return empty DataFrame if no data to process
        else:
            return pd.concat(normalized_df.tolist(), ignore_index=True)
    except KeyError:
        # Handle the case where the specified column does not exist
        return pd.DataFrame(columns=df_columns)
