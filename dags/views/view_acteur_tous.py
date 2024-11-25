from datetime import datetime
from logging import getLogger

from airflow import DAG
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook

logger = getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 11, 24),
    "catchup": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
}
SCHEDULE_INTERVAL = "0 2 * * *"
VIEW_NAME = "qfdmo_vue_acteur_tous"


def SQL_VIEW_CREATE_QUERY_get() -> str:
    """Construit la requête SQL pour la vue matérialisée acteur_all"""
    # Champs communs à toutes les tables, on prend au mieux avec COALESCE
    fields_on_all = [
        # IDs
        "identifiant_unique",
        "identifiant_externe",
        "acteur_type_id",
        "source_id",
        "action_principale_id",
        # Noms
        "nom",
        "nom_commercial",
        "nom_officiel",
        # GEO
        "adresse",
        "adresse_complement",
        "code_postal",
        "location",
        "ville",
        # Contact
        "telephone",
        "email",
        "url",
        "horaires_description",
        "horaires_osm",
        "uniquement_sur_rdv",
        # MISC
        "statut",
        "naf_principal",
        "siret",
        "public_accueilli",
        "exclusivite_de_reprisereparation",
    ]
    selected = ",\n".join(
        [f"COALESCE(da.{x}, ra.{x}, a.{x}) AS {x}" for x in fields_on_all]
    )
    # dernier champ sélectionné: parent_id qui n'existe que dans revisionacteur
    selected += ",\nra.parent_id AS parent_id,\n"
    selected += """da.identifiant_unique IS NOT NULL AS est_dans_displayedacteur,
                    ra.identifiant_unique IS NOT NULL AS est_dans_revisionacteur,
                    a.identifiant_unique IS NOT NULL AS est_dans_acteur"""

    query = f"""
    -- Il n'existe pas aujourdhui de CREATE OR REPLACE MATERIALIZED VIEW
    -- d'où l'autre requête DROP IF EXISTS avant de créer
    CREATE MATERIALIZED VIEW {VIEW_NAME} AS (
        WITH acteur_all AS (
            SELECT
                {selected}
                    FROM qfdmo_displayedacteur AS da
                    FULL OUTER JOIN qfdmo_revisionacteur AS ra
                        ON da.identifiant_unique = ra.identifiant_unique
                    FULL OUTER JOIN qfdmo_acteur AS a
                        ON da.identifiant_unique = a.identifiant_unique
        ), parent_ids AS (
                SELECT DISTINCT parent_id AS id
                FROM qfdmo_revisionacteur
        )
        SELECT
            -- ne pas faire un lazy * car ceci sélectionne des champs génériques
            -- présents sur plusieurs tables (ex: url) ce qui cause des erreurs
            acteur_all.*,
            ST_Y(acteur_all.location) AS location_lat,
            ST_X(acteur_all.location) AS location_long,
            -- Si l'identifiant est dans la liste des parent_ids, alors c'est un parent
            CASE
                WHEN identifiant_unique IN (SELECT id FROM parent_ids) THEN TRUE
                ELSE FALSE
            END AS est_parent,
            -- Les codes pour être plus pratique ques les ids
            s.code AS source_code,
            atype.code AS acteur_type_code
        FROM acteur_all
        LEFT JOIN qfdmo_source AS s ON s.id = acteur_all.source_id
        LEFT JOIN qfdmo_acteurtype AS atype ON atype.id = acteur_all.acteur_type_id
    )"""
    return query


SQL_VIEW_DROP_QUERY = f"DROP MATERIALIZED VIEW IF EXISTS {VIEW_NAME};"
SQL_VIEW_CREATE_QUERY = SQL_VIEW_CREATE_QUERY_get()

DESCRIPTION = f"""Vue matérialisée SQL {VIEW_NAME} pour afficher tous les acteurs
dans la base de données à partir des tables: qdfdmo_displayedacteur,
qfdmo_revisionacteur, et qfdmo_acteurs avec de la réconciliation sur les 3 tables
et des champs calculés (ex: is_parent)"""

with DAG(
    dag_id="view_acteur_all",
    tags=["view", "vue", "acteur", "displayed", "revision", "all", "tout", "sql"],
    default_args=DEFAULT_ARGS,
    schedule_interval=SCHEDULE_INTERVAL,
    dag_display_name="Vue - Acteur - Tous les acteurs",
    description=DESCRIPTION,
    doc_md=f"""
    {DESCRIPTION}

    Construction de la vue SQL:
    ```{SQL_VIEW_CREATE_QUERY}```
    """,
):

    @task
    def view_acteur_all_drop_if_exists_and_create_task():
        """Tâche qui supprime (si existe) et crée la vue matérialisée view_acteur_all
        La tâche gère les 2 opérations car:
            - logiquement elles sont liées (pas l'un sans l'autre)
            - elles sont toutes les 2 petites et rapides
            - on veut éviter d'avoir à parcourir les logs de 2 petites tâches
        """
        pg_hook = PostgresHook(postgres_conn_id="qfdmo_django_db")

        with pg_hook.get_conn() as conn:
            with conn.cursor() as cursor:
                logger.info(f"SQL_VIEW_DROP_QUERY:\n{SQL_VIEW_DROP_QUERY}")
                cursor.execute(SQL_VIEW_DROP_QUERY)
                conn.commit()

                logger.info(f"SQL_VIEW_CREATE_QUERY:\n{SQL_VIEW_CREATE_QUERY}")
                cursor.execute(SQL_VIEW_CREATE_QUERY)
                conn.commit()

    view_acteur_all_drop_if_exists_and_create_task()

# Pour débugger facilement via CLI
if __name__ == "__main__":
    print("SQL_VIEW_DROP_QUERY:\n", SQL_VIEW_DROP_QUERY)
    print("SQL_VIEW_CREATE_QUERY:\n", SQL_VIEW_CREATE_QUERY)
