import logging

import pandas as pd
from shared.tasks.database_logic.db_manager import PostgresConnectionManager

from utils import logging_utils as log

logger = logging.getLogger(__name__)


def read_data_from_postgres(**kwargs):
    table_name = kwargs["table_name"]
    engine = PostgresConnectionManager().engine

    chunks = pd.read_sql_table(table_name, engine, chunksize=10000)
    df = pd.concat([chunk for chunk in chunks]).replace({pd.NA: None})
    df.reset_index(drop=True, inplace=True)

    if df.empty:
        raise ValueError(f"DB: pas de données pour table {table_name}")
    log.preview(f"df pour la table {table_name}", df)
    return df
