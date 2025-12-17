import logging
import subprocess
import tempfile

from utils.django import django_setup_full

logger = logging.getLogger(__name__)

django_setup_full()

# TODO: can we use APP
INCLUDE_TABLES_STARTING_WITH = [
    "auth_",
    "django_",
    "dsfr_",
    "qfdmd_",
    "qfdmo_",
    "sites_faciles_",
    "taggit_",
    "wagtail",
]
EXCLUDE_TABLES = [
    "qfdmo_acteur_acteur_services",
    "qfdmo_acteur_labels",
    "qfdmo_acteur",
    "qfdmo_displayedacteur_acteur_services",
    "qfdmo_displayedacteur_labels",
    "qfdmo_displayedacteur_sources",
    "qfdmo_displayedacteur",
    "qfdmo_displayedperimetreadomicile",
    "qfdmo_displayedpropositionservice_sous_categories",
    "qfdmo_displayedpropositionservice",
    "qfdmo_perimetreadomicile",
    "qfdmo_propositionservice_sous_categories",
    "qfdmo_propositionservice",
    "qfdmo_revisionacteur_acteur_services",
    "qfdmo_revisionacteur_labels",
    "qfdmo_revisionacteur",
    "qfdmo_revisionperimetreadomicile",
    "qfdmo_revisionpropositionservice_sous_categories",
    "qfdmo_revisionpropositionservice",
    "qfdmo_vueacteur_acteur_services",
    "qfdmo_vueacteur_labels",
    "qfdmo_vueacteur_sources",
    "qfdmo_vueacteur",
    "qfdmo_vueperimetreadomicile",
    "qfdmo_vuepropositionservice_sous_categories",
    "qfdmo_vuepropositionservice",
]


def _get_webapp_dsns():
    from django.conf import settings

    dsn_webapp_db = settings.DATABASE_URL
    dsn_webapp_sample_db = settings.DB_WEBAPP_SAMPLE

    return dsn_webapp_db, dsn_webapp_sample_db


def _get_all_tables(cursor):
    cursor.execute(
        """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """
    )
    tables = [row[0] for row in cursor.fetchall()]
    return tables


def copy_db_schema():
    from django.db import connections

    dsn_webapp_db, dsn_webapp_sample_db = _get_webapp_dsns()

    # Remove all tables from webapp_sample without needing rights on the DB
    logger.info("🗑️  Suppression de toutes les tables de webapp_sample...")
    try:
        with connections["webapp_sample"].cursor() as cursor:
            # Get all tables from the public schema
            tables = _get_all_tables(cursor)

            if tables:
                logger.info(f"📋 {len(tables)} tables trouvées à supprimer")
                # Remove each table with CASCADE to avoid foreign key constraints errors
                for table in tables:
                    try:
                        cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
                        logger.info(f"  ✓ Table {table} supprimée")
                    except Exception as e:
                        logger.warning(
                            f"  ⚠ Erreur lors de la suppression de {table}: {e}"
                        )
                logger.info("✅ Toutes les tables supprimées")
            else:
                logger.info("ℹ️  Aucune table à supprimer")
    except Exception as e:
        logger.warning(f"⚠️  Erreur lors de la suppression des tables: {e}")
        logger.info("ℹ️  Continuation malgré l'erreur...")

    # Step 1: Copy schema only (structure without data)
    logger.info("📐 Copie du schéma uniquement (structure sans données)...")
    schema_dump_cmd = [
        "pg_dump",
        "-d",
        dsn_webapp_db,
        "--schema=public",
        "--schema-only",
        "--no-owner",
        "--no-acl",
        "--format=custom",
    ]

    with tempfile.NamedTemporaryFile(suffix=".schema.dump") as tmp_schema_file:
        schema_dump_file = tmp_schema_file.name

        # Create schema dump
        with open(schema_dump_file, "wb") as f:
            subprocess.run(
                schema_dump_cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                check=True,
            )
        logger.info("✅ Dump du schéma créé")

        # Restore schema to destination
        subprocess.run(
            [
                "pg_restore",
                "-d",
                dsn_webapp_sample_db,
                "--schema=public",
                "--clean",
                "--no-owner",
                "--if-exists",
                "--no-acl",
                "--no-privileges",
                schema_dump_file,
            ],
            check=False,
        )
        logger.info("✅ Schéma restauré dans la base de destination")


def copy_db_data():
    from django.db import connections

    dsn_webapp_db, dsn_webapp_sample_db = _get_webapp_dsns()

    logger.info(
        f"📊 Copie des données pour {len(INCLUDE_TABLES_STARTING_WITH)} tables..."
    )

    # Get tables starting with INCLUDE_TABLES_STARTING_WITH from
    # information_schema.tables
    with connections["webapp_sample"].cursor() as cursor:
        cursor.execute("SELECT table_name FROM information_schema.tables")
        tables = [table[0] for table in cursor.fetchall()]

    # filter tables starting with INCLUDE_TABLES_STARTING_WITH
    tables = [
        table
        for table in tables
        if any(table.startswith(prefix) for prefix in INCLUDE_TABLES_STARTING_WITH)
    ]
    logger.info(f"✅ {len(tables)} tables trouvées")

    # filter tables not in EXCLUDE_TABLES
    tables = [table for table in tables if table not in EXCLUDE_TABLES]
    logger.info(f"✅ {len(tables)} tables trouvées après filtrage")

    # Create data-only dump
    data_dump_cmd = [
        "pg_dump",
        "-d",
        dsn_webapp_db,
        "--schema=public",
        "--data-only",
        "--no-owner",
        "--no-acl",
        "--format=custom",
    ]

    for table in tables:
        data_dump_cmd.append("--table")
        data_dump_cmd.append(f"public.{table}")

    tmp_data_file = tempfile.NamedTemporaryFile(suffix=".dump", delete=False)
    data_dump_file = tmp_data_file.name
    tmp_data_file.close()  # Fermer le fichier pour permettre l'écriture

    with tempfile.NamedTemporaryFile(suffix=".dump", delete=False) as tmp_data_file:
        data_dump_file = tmp_data_file.name

        # Create data dump for this table
        with open(data_dump_file, "wb") as f:
            subprocess.run(
                data_dump_cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                check=True,
            )

            # Restore data to destination
            subprocess.run(
                [
                    "pg_restore",
                    "-d",
                    dsn_webapp_sample_db,
                    "--schema=public",
                    "--no-owner",
                    "--no-acl",
                    "--no-privileges",
                    "--disable-triggers",
                    data_dump_file,
                ],
                check=False,
            )
            logger.info(f"✅ Données de {table} copiées avec succès")

    logger.info("✅ Copie terminée avec succès")


def copy_displayed_data_from_warehouse():
    pass
