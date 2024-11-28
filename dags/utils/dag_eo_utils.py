import json
import logging
from datetime import datetime

from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from sources.config import shared_constants as constants

logger = logging.getLogger(__name__)


def insert_dagrun_and_process_df(df_acteur_updates, metadata, dag_name, run_name):
    if df_acteur_updates.empty:
        return
    engine = PostgresConnectionManager().engine
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
    df_acteur_updates["status"] = constants.DAGRUN_TOVALIDATE
    df_acteur_updates[["row_updates", "dag_run_id", "change_type", "status"]].to_sql(
        "qfdmo_dagrunchange",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )
