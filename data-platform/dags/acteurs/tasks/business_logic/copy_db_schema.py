import logging

from utils.django import django_setup_full

from .copy_utils import dump_and_restore_db

logger = logging.getLogger(__name__)

django_setup_full()


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
    from django.conf import settings
    from django.db import connections

    dsn_webapp_db = settings.DATABASE_URL
    dsn_webapp_sample_db = settings.DB_WEBAPP_SAMPLE

    # Remove all tables from webapp_sample without needing rights on the DB
    logger.info("🗑️  Suppression de toutes les tables de webapp_sample...")
    try:
        with connections["webapp_sample"].cursor() as cursor:
            # Get all tables from the public schema
            tables = _get_all_tables(cursor)

            logger.info(f"📋 {len(tables)} tables trouvées à supprimer")
            # Remove each table with CASCADE to avoid foreign key constraints errors
            for table in tables:
                try:
                    cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
                    logger.info(f"  ✓ Table {table} supprimée")
                except Exception as e:
                    logger.warning(f"  ⚠ Erreur lors de la suppression de {table}: {e}")
    except Exception as e:
        logger.warning(f"⚠️  Erreur lors de la suppression des tables: {e}")
        logger.info("ℹ️  Continuation malgré l'erreur...")

    # Step 1: Copy schema only (structure without data)
    logger.info("📐 Copie du schéma uniquement (structure sans données)...")
    dump_and_restore_db(
        source_dsn=dsn_webapp_db,
        dest_dsn=dsn_webapp_sample_db,
        schema_only=True,
    )
    logger.info("✅ Schéma restauré dans la base de destination")
