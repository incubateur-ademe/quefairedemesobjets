import logging

from utils.django import django_setup_full

from .copy_utils import dump_and_restore_db

logger = logging.getLogger(__name__)

django_setup_full()


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


def copy_db_data():
    import importlib

    from django.conf import settings
    from django.db import connections

    dsn_webapp_db = settings.DATABASE_URL
    dsn_webapp_sample_db = settings.DB_WEBAPP_SAMPLE

    logger.info("📊 Copie des données...")

    # Get tables and filter them
    with connections["webapp_sample"].cursor() as cursor:
        cursor.execute("SELECT table_name FROM information_schema.tables")
        tables = [table[0] for table in cursor.fetchall()]

    # Get app labels from main Django settings (not Airflow settings)
    # Import the main settings module to get the full INSTALLED_APPS list
    main_settings = importlib.import_module("core.settings")

    # Extract app labels from INSTALLED_APPS
    table_prefixes = set()
    for app in main_settings.INSTALLED_APPS:
        # Get the last part of the app path (e.g., "qfdmd" from "qfdmd")
        # or "auth" from "django.contrib.auth"
        app_label = app.split(".")[-1]
        table_prefixes.add(app_label)

    # Add "django" for system tables
    table_prefixes.add("django")
    tables = [
        table
        for table in tables
        if any(table.startswith(prefix) for prefix in table_prefixes)
    ]
    logger.info(f"✅ {len(tables)} tables trouvées")

    # filter tables not in EXCLUDE_TABLES
    tables = [table for table in tables if table not in EXCLUDE_TABLES]
    logger.info(f"✅ {len(tables)} tables trouvées après filtrage")
    for table in tables:
        logger.info(f"✅ {table} va être copiée")

    # Create data-only dump
    dump_and_restore_db(
        source_dsn=dsn_webapp_db,
        dest_dsn=dsn_webapp_sample_db,
        tables=tables,
        data_only=True,
    )

    logger.info("✅ Copie terminée avec succès")
