import logging

from utils.django import django_setup_full

from .copy_utils import dump_and_restore_db

logger = logging.getLogger(__name__)

django_setup_full()


EXPOSURE_TABLE_MAPPINGS = {
    "exposure_sample_displayedacteur": "qfdmo_displayedacteur",
    "exposure_sample_displayedpropositionservice": "qfdmo_displayedpropositionservice",
    "exposure_sample_displayedpropositionservice_sous_categories": (
        "qfdmo_displayedpropositionservice_sous_categories"
    ),
    "exposure_sample_displayedacteur_acteur_services": (
        "qfdmo_displayedacteur_acteur_services"
    ),
    "exposure_sample_displayedacteur_labels": "qfdmo_displayedacteur_labels",
    "exposure_sample_displayedacteur_sources": "qfdmo_displayedacteur_sources",
    "exposure_sample_displayedperimetreadomicile": "qfdmo_displayedperimetreadomicile",
}


def _drop_exposure_tables_from_webapp_sample():
    from django.db import connections

    with connections["webapp_sample"].cursor() as cursor:
        for table in EXPOSURE_TABLE_MAPPINGS.keys():
            try:
                cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
                logger.info(f"  ✓ Table {table} supprimée")
            except Exception as e:
                logger.warning(f"  ⚠ Erreur lors de la suppression de {table}: {e}")


def copy_displayed_data_from_warehouse():
    """
    Copy data from displayed* tables from warehouse to webapp_sample.

    Étapes :
    1. Make sure exposure target tables doesn't exists in webapp_sample
    2. Dump exposure_sample_* tables from warehouse
    3. Restore the dump in webapp_sample (create the exposure_sample_* tables)
    4. Copy the content of the exposure_sample_* tables to the qfdmo_* tables
    5. Delete the exposure_sample_* tables from webapp_sample
    """
    from django.conf import settings
    from django.db import connections

    dsn_warehouse_db = settings.DB_WAREHOUSE
    dsn_webapp_sample_db = settings.DB_WEBAPP_SAMPLE

    # Step 1: Make sure exposure target tables doesn't exists in webapp_sample
    logger.info("🗑️  Suppression des tables exposure_sample_* dans webapp_sample...")
    _drop_exposure_tables_from_webapp_sample()

    # Step 2: Dump exposure_sample_* tables from warehouse
    logger.info("📥 Import du dump dans webapp_sample...")
    dump_and_restore_db(
        source_dsn=dsn_warehouse_db,
        dest_dsn=dsn_webapp_sample_db,
        tables=list(EXPOSURE_TABLE_MAPPINGS.keys()),
    )
    logger.info("✅ Données importées dans webapp_sample")

    # Step 4: Copy the content of the exposure_sample_* tables to the qfdmo_* tables
    logger.info("📋 Copie des données vers les tables qfdmo_*...")
    with connections["webapp_sample"].cursor() as cursor:
        for source_table, dest_table in EXPOSURE_TABLE_MAPPINGS.items():
            cursor.execute(f"INSERT INTO {dest_table} SELECT * FROM {source_table}")
            logger.info(
                f"  ✓ {cursor.rowcount} lignes copiées de {source_table} vers"
                f" {dest_table}"
            )

    # Step 5: Delete the exposure_sample_* tables from webapp_sample
    logger.info("🗑️  Suppression des tables exposure_sample_* de webapp_sample...")
    _drop_exposure_tables_from_webapp_sample()

    logger.info(
        "✅ Copie des données displayed* de warehouse vers webapp_sample terminée avec"
        " succès"
    )
