import json
import logging
from datetime import datetime

from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from sources.config import shared_constants as constants

logger = logging.getLogger(__name__)


def insert_suggestion_and_process_df(df_acteur_updates, metadata, dag_name, run_name):
    if df_acteur_updates.empty:
        return
    engine = PostgresConnectionManager().engine
    current_date = datetime.now()
    logger.warning(dag_name)
    logger.warning(run_name)
    logger.warning(constants.SUGGESTION_SOURCE)
    logger.warning(constants.SUGGESTION_ATRAITER)
    logger.warning(json.dumps(metadata))
    with engine.connect() as conn:
        # Insert a new suggestion
        result = conn.execute(
            """
            INSERT INTO qfdmo_suggestioncohorte
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
                constants.SUGGESTION_SOURCE,  # FIXME: spécialiser les sources
                constants.SUGGESTION_ATRAITER,
                json.dumps(metadata),
                current_date,
                current_date,
            ),
        )
        suggestion_cohorte_id = result.fetchone()[0]

    # Insert dag_run_change
    df_acteur_updates["type_action"] = df_acteur_updates["event"]
    df_acteur_updates["suggestion_cohorte_id"] = suggestion_cohorte_id
    df_acteur_updates["statut"] = constants.SUGGESTION_ATRAITER
    df_acteur_updates[
        ["suggestion", "suggestion_cohorte_id", "type_action", "statut"]
    ].to_sql(
        "qfdmo_suggestionunitaire",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )
