import logging

from utils.django import django_setup_full

logger = logging.getLogger(__name__)

django_setup_full()


def replace_acteur_table(
    schema_django: str,
    prefix_django: str,
    schema_dbt: str,
    prefix_dbt: str,
    tables=[
        "acteur",
        "acteur_acteur_services",
        "acteur_labels",
        "acteur_sources",
        "propositionservice",
        "propositionservice_sous_categories",
    ],
):
    from django.db import connection

    with connection.cursor() as cursor:
        logger.warning("Open a transaction")
        cursor.execute("BEGIN")
        try:
            for table in tables:
                # copie de la table de schema public -> schema warehouse
                # including indexes
                cursor.execute(
                    f"DROP TABLE IF EXISTS {schema_django}.{prefix_dbt}{table}"
                )
                cursor.execute(
                    f"CREATE TABLE {schema_django}.{prefix_dbt}{table}"
                    f" (LIKE {schema_dbt}.{prefix_dbt}{table} INCLUDING INDEXES)"
                )
                cursor.execute(
                    f"INSERT INTO {schema_django}.{prefix_dbt}{table} "
                    f"SELECT * FROM {schema_dbt}.{prefix_dbt}{table}"
                )

                logger.warning(
                    f"Renaming {prefix_django}{table}"
                    f" to {prefix_django}{table}_to_remove"
                )
                cursor.execute(
                    f"ALTER TABLE IF EXISTS {prefix_django}{table}"
                    f" RENAME TO {prefix_django}{table}_to_remove"
                )
                logger.warning(
                    f"Renaming {prefix_dbt}{table} to {prefix_django}{table}"
                )
                cursor.execute(
                    f"ALTER TABLE {prefix_dbt}{table} RENAME TO {prefix_django}{table}"
                )
                logger.warning(f"Removing {prefix_django}{table}_to_remove")
                cursor.execute(
                    f"DROP TABLE IF EXISTS {prefix_django}{table}_to_remove CASCADE"
                )
            logger.warning("Commit the transaction")
            cursor.execute("COMMIT")
        except Exception as e:
            logger.warning("Rollback the transaction")
            cursor.execute("ROLLBACK")
            raise e
