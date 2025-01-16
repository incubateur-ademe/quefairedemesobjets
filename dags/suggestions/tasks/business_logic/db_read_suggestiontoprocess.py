from airflow.providers.postgres.hooks.postgres import PostgresHook
from sources.config import shared_constants as constants


def get_first_suggetsioncohorte_to_insert():
    hook = PostgresHook(postgres_conn_id="qfdmo_django_db")
    row = hook.get_first(
        f"""
        SELECT * FROM data_suggestioncohorte
        WHERE statut = '{constants.SUGGESTION_ATRAITER}'
        LIMIT 1
        """
    )
    return row


def db_read_suggestiontoprocess(**kwargs):
    return bool(get_first_suggetsioncohorte_to_insert())
