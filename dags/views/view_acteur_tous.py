import time
from logging import getLogger
from pathlib import Path

from airflow import DAG
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago

logger = getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
}
SCHEDULE = "0 2 * * *"
VIEW_NAME = "qfdmo_vue_acteur_tous"

DIR_CURRENT = Path(__file__).parent
SQL_VIEW_DROP_QUERY = f"DROP MATERIALIZED VIEW IF EXISTS {VIEW_NAME};"
SQL_VIEW_CREATE_QUERY = Path(DIR_CURRENT / "sql" / "view_acteur_tous.sql").read_text()

DESCRIPTION = f"""Vue matérialisée SQL {VIEW_NAME} pour afficher tous les acteurs
dans la base de données à partir des tables: qdfdmo_displayedacteur,
qfdmo_revisionacteur, et qfdmo_acteurs avec de la réconciliation sur les 3 tables
et des champs calculés (ex: is_parent)"""

with DAG(
    dag_id="view_acteur_all",
    tags=["view", "vue", "acteur", "displayed", "revision", "all", "tout", "sql"],
    default_args=DEFAULT_ARGS,
    catchup=False,
    schedule=SCHEDULE,
    dag_display_name="Vue - Acteur - Tous les acteurs",
    description=DESCRIPTION,
    doc_md=f"""
    {DESCRIPTION}

    Construction de la vue SQL:
    ```{SQL_VIEW_CREATE_QUERY}```
    """,
):

    def show_enable_parallel_hash(cursor, message):
        cursor.execute("SHOW enable_parallel_hash;")
        logger.info(f"{message}: enable_parallel_hash: {cursor.fetchone()}")

    @task
    def view_acteur_tous_drop_if_exists_and_create_task():
        """Tâche qui supprime (si existe) et crée la vue matérialisée view_acteur_all
        La tâche gère les 2 opérations car:
            - logiquement elles sont liées (pas l'un sans l'autre)
            - elles sont toutes les 2 petites et rapides
            - on veut éviter d'avoir à parcourir les logs de 2 petites tâches
        """
        pg_hook = PostgresHook(postgres_conn_id="qfdmo_django_db")

        with pg_hook.get_conn() as conn:
            with conn.cursor() as cursor:
                # Workaround for
                # https://stackoverflow.com/questions/54351783/duplicate-key-value-violates-unique-constraint-postgres-error-when-trying-to-c
                show_enable_parallel_hash(cursor, "before changing")
                cursor.execute("SET enable_parallel_hash = off;")
                show_enable_parallel_hash(cursor, "after changing")

                logger.info("Dropping view: started 🟡")
                logger.info(f"SQL_VIEW_DROP_QUERY:\n{SQL_VIEW_DROP_QUERY}")
                cursor.execute(SQL_VIEW_DROP_QUERY)
                conn.commit()
                logger.info("Dropping view: completed 🟢")

                # A pause to ensure PostgreSQL internal state is fully updated
                # and ready to accept new view creation
                time.sleep(5)

                logger.info("Creating view: started 🟡")
                logger.info(f"SQL_VIEW_CREATE_QUERY:\n{SQL_VIEW_CREATE_QUERY}")
                cursor.execute(SQL_VIEW_CREATE_QUERY)
                conn.commit()
                logger.info("Creating view: completed 🟢")

                cursor.execute("SET enable_parallel_hash = on;")
                show_enable_parallel_hash(cursor, "setting back")

    view_acteur_tous_drop_if_exists_and_create_task()
