import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook
from utils import logging_utils as log


def read_data_from_postgres(**kwargs):
    table_name = kwargs["table_name"]
    pg_hook = PostgresHook(postgres_conn_id="qfdmo_django_db")
    engine = pg_hook.get_sqlalchemy_engine()
    df = pd.read_sql_table(table_name, engine).replace({pd.NA: None})
    if df.empty:
        raise ValueError(f"DB: pas de données pour table {table_name}")
    log.preview(f"df pour la table {table_name}", df)
    return df
