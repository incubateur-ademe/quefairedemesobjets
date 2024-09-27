import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook


def read_data_from_postgres(**kwargs):
    table_name = kwargs["table_name"]
    pg_hook = PostgresHook(postgres_conn_id="qfdmo-django-db")
    engine = pg_hook.get_sqlalchemy_engine()
    df = pd.read_sql_table(table_name, engine)
    return df
