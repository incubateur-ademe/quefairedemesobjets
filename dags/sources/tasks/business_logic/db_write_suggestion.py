import json
import logging
from datetime import datetime

import pandas as pd
from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from sources.config import shared_constants as constants

logger = logging.getLogger(__name__)


def db_write_suggestion(
    dag_name: str,
    run_id: str,
    df_acteur_to_create: pd.DataFrame,
    df_acteur_to_delete: pd.DataFrame,
    df_acteur_to_update: pd.DataFrame,
):

    metadata = {}

    run_name = run_id.replace("__", " - ")

    insert_suggestion(
        df=df_acteur_to_create,
        metadata=metadata,
        dag_name=f"{dag_name} - AJOUT",
        run_name=run_name,
        action_type=constants.SUGGESTION_SOURCE_AJOUT,
    )
    insert_suggestion(
        df=df_acteur_to_delete,
        metadata=metadata,
        dag_name=f"{dag_name} - SUPRESSION",
        run_name=run_name,
        action_type=constants.SUGGESTION_SOURCE_SUPRESSION,
    )
    insert_suggestion(
        df=df_acteur_to_update,
        metadata=metadata,
        dag_name=f"{dag_name} - MISES A JOUR",
        run_name=run_name,
        action_type=constants.SUGGESTION_SOURCE_MISESAJOUR,
    )


def insert_suggestion(
    df: pd.DataFrame, metadata: dict, dag_name: str, run_name: str, action_type: str
):
    if df.empty:
        return
    engine = PostgresConnectionManager().engine
    current_date = datetime.now()

    with engine.connect() as conn:
        # Insert a new suggestion
        result = conn.execute(
            """
            INSERT INTO data_suggestioncohorte
            (
                identifiant_action,
                identifiant_execution,
                type_action,
                statut,
                metadata,
                cree_le,
                modifie_le
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING ID;
        """,
            (
                dag_name,
                run_name,
                action_type,
                constants.SUGGESTION_AVALIDER,
                json.dumps(metadata),
                current_date,
                current_date,
            ),
        )
        suggestion_cohorte_id = result.fetchone()[0]

    # Insert dag_run_change
    df["type_action"] = action_type
    df["suggestion_cohorte_id"] = suggestion_cohorte_id
    df["statut"] = constants.SUGGESTION_AVALIDER
    df[["suggestion", "suggestion_cohorte_id", "type_action", "statut"]].to_sql(
        "data_suggestionunitaire",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )
