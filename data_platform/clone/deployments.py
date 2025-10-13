"""Script de déploiement pour tous les flows Prefect."""

# from data_platform.clone.flows.clone_ae_etablissement import clone_ae_etablissement
# from data_platform.clone.flows.clone_ae_unite_legale import clone_ae_unite_legale
# from data_platform.clone.flows.clone_ban_adresses import clone_ban_adresses
# from data_platform.clone.flows.clone_ban_lieux_dits import clone_ban_lieux_dits
from data_platform.clone.flows.clone_external_table import clone_external_table
from data_platform.shared.config.tags import TAGS

deploy_clone_ae_etablissement = clone_external_table.to_deployment(
    name="Cloner - AE - Etablissement",
    description="Clone la table etablissement de l'Annuaire des Entreprises",
    tags=[
        TAGS.ENRICH,
        TAGS.CLONE,
        TAGS.ANNAIRE_ENTREPRISE,
        TAGS.ETABLISSEMENT,
        TAGS.SIRET,
    ],
    parameters={
        "dry_run": False,
        "table_kind": "ae_etablissement",
        "data_endpoint": "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockEtablissement_utf8.zip",
        "clone_method": "stream_directly",
        "file_downloaded": "StockEtablissement_utf8.zip",
        "file_unpacked": "StockEtablissement_utf8.csv",
        "delimiter": ",",
    },
    # Définir un schedule si besoin
    # cron="0 2 * * *",  # Tous les jours à 2h
)


deploy_clone_ae_unite_legale = clone_external_table.to_deployment(
    name="Cloner - AE - Unite Legale",
    description="Clone la table unite_legale de l'Annuaire des Entreprises",
    tags=[
        TAGS.ENRICH,
        TAGS.CLONE,
        TAGS.ANNAIRE_ENTREPRISE,
        TAGS.UNITE_LEGALE,
        TAGS.SIRET,
    ],
    parameters={
        "dry_run": False,
        "table_kind": "ae_unite_legale",
        "data_endpoint": "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockUniteLegale_utf8.zip",
        "clone_method": "stream_directly",
        "file_downloaded": "StockUniteLegale_utf8.zip",
        "file_unpacked": "StockUniteLegale_utf8.csv",
        "delimiter": ",",
    },
    # Définir un schedule si besoin
    # cron="0 2 * * *",  # Tous les jours à 2h
)


deploy_clone_ban_adresses = clone_external_table.to_deployment(
    name="Cloner - BAN - Adresses",
    description=(
        "Clone la table 'adresses' de la Base Adresse Nationale (BAN) dans notre DB"
    ),
    tags=[
        TAGS.ENRICH,
        TAGS.CLONE,
        TAGS.BAN,
        TAGS.ADRESSES,
    ],
    parameters={
        "dry_run": False,
        "table_kind": "ban_adresses",
        "data_endpoint": (
            "https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/"
            "adresses-france.csv.gz"
        ),
        "clone_method": "stream_directly",
        "file_downloaded": "adresses-france.csv.gz",
        "file_unpacked": "adresses-france.csv",
        "delimiter": ",",
    },
)


deploy_clone_ban_lieux_dits = clone_external_table.to_deployment(
    name="Cloner - BAN - Lieux-dits",
    description=(
        "Clone la table 'lieux_dits' de la Base Adresse Nationale (BAN) dans notre DB"
    ),
    tags=[
        TAGS.ENRICH,
        TAGS.CLONE,
        TAGS.BAN,
        TAGS.LIEUX_DITS,
    ],
    parameters={
        "dry_run": False,
        "table_kind": "ban_lieux_dits",
        "data_endpoint": (
            "https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/"
            "lieux-dits-beta-france.csv.gz"
        ),
        "clone_method": "stream_directly",
        "file_downloaded": "lieux-dits-beta-france.csv.gz",
        "file_unpacked": "lieux-dits-beta-france.csv",
        "delimiter": ",",
    },
)
