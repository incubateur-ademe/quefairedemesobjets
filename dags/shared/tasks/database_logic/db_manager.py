from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy.engine import Engine


class PostgresConnectionManager:
    """
    Singleton class to manage the connection to the Postgres database.
    use the connecter qfdmo_django_db by default
    this connecter is set by using env variable AIRFLOW_CONN_QFDMO_DJANGO_DB
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PostgresConnectionManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, postgres_conn_id="qfdmo_django_db"):
        if not hasattr(self, "initialized"):  # Pour éviter la réinitialisation
            self.postgres_conn_id = postgres_conn_id
            self.engine = self._create_engine()
            self.initialized = True

    def _create_engine(self) -> Engine:
        pg_hook = PostgresHook(postgres_conn_id=self.postgres_conn_id)
        return pg_hook.get_sqlalchemy_engine()
