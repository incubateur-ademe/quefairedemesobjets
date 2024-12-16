import logging
from datetime import datetime

import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def _table_name(dag_id: str, dag_run_id: str, task_id: str, dataset_name: str):
    # dag_run_id remove str before __
    dag_run_id = dag_run_id.split("__")[1]
    timestamp = datetime.strptime(dag_run_id, "%Y-%m-%dT%H:%M:%S.%f%z")
    timestamp = int(timestamp.timestamp())
    return f"{dag_id[:10]}_{timestamp}_{task_id[:10]}_{dataset_name}"


class PostgresConnectionManager:
    """
    Singleton class to manage the connections to the Postgres database.
    use the connecters qfdmo_django_db and qfdmo_data_db by default
    this connecter is set by using env variable AIRFLOW_CONN_QFDMO_DJANGO_DB
    and AIRFLOW_CONN_QFDMO_DATA_DB
    """

    # FIXME : créer une migration pour créer la ase de données qfdmodata

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PostgresConnectionManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, django_conn_id="qfdmo_django_db", data_conn_id="qfdmo_data_db"):
        if not hasattr(self, "initialized"):  # Pour éviter la réinitialisation
            self.django_conn_id = django_conn_id
            self.data_conn_id = data_conn_id
            self.django_engine = self._create_engine(self.django_conn_id)
            self.data_engine = self._create_engine(self.data_conn_id)
            self.initialized = True

    def _create_engine(self, engine_id: str) -> Engine:
        pg_hook = PostgresHook(postgres_conn_id=engine_id)
        return pg_hook.get_sqlalchemy_engine()

    def write_data_xcom(
        self,
        dag_id: str,
        dag_run_id: str,
        task_id: str,
        dataset_name: str,
        df: pd.DataFrame,
    ):

        table_name = _table_name(dag_id, dag_run_id, task_id, dataset_name)
        df.to_sql(table_name, self.data_engine, if_exists="replace", index=False)

    def read_data_xcom(
        self, dag_id: str, dag_run_id: str, task_id: str, dataset_name: str
    ) -> pd.DataFrame:
        table_name = _table_name(dag_id, dag_run_id, task_id, dataset_name)
        return pd.read_sql(f"SELECT * FROM {table_name}", self.data_engine)
