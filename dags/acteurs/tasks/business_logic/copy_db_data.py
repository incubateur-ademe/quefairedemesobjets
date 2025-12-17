import logging
import subprocess
import tempfile

from utils.django import django_setup_full

logger = logging.getLogger(__name__)

django_setup_full()

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


def copy_db_data():
    from django.conf import settings
    from django.db import connections

    dsn_webapp_db = settings.DATABASE_URL
    dsn_webapp_sample_db = settings.DB_WEBAPP_SAMPLE

    logger.info("📊 Copie des données...")

    # Get tables starting with INCLUDE_TABLES_STARTING_WITH from
    # information_schema.tables
    with connections["webapp_sample"].cursor() as cursor:
        cursor.execute("SELECT table_name FROM information_schema.tables")
        tables = [table[0] for table in cursor.fetchall()]

    # filter tables starting with INCLUDE_TABLES_STARTING_WITH
    tables = [
        table
        for table in tables
        if any(table.startswith(prefix) for prefix in settings.INSTALLED_APPS)
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
