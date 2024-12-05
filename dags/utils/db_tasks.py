import pandas as pd
from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from utils import logging_utils as log


def read_data_from_postgres(**kwargs):
    table_name = kwargs["table_name"]
    engine = PostgresConnectionManager().engine
    df = pd.read_sql_table(table_name, engine).replace({pd.NA: None})
    if df.empty:
        raise ValueError(f"DB: pas de données pour table {table_name}")
    log.preview(f"df pour la table {table_name}", df)
    return df
