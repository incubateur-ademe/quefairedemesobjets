import pandas as pd
from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from sources.config import shared_constants as constants


def get_first_suggetsioncohorte_to_insert():
    engine = PostgresConnectionManager().engine

    # get first cohorte suggestion to process as a dict
    suggestion_cohorte = pd.read_sql_query(
        f"""
        SELECT * FROM data_suggestioncohorte
        WHERE statut = '{constants.SUGGESTION_ATRAITER}'
        LIMIT 1
        """,
        engine,
    )
    if suggestion_cohorte.empty:
        return None
    return suggestion_cohorte.to_dict(orient="records")[0]


def db_read_suggestiontoprocess(**kwargs):
    return bool(get_first_suggetsioncohorte_to_insert())
