import logging
from itertools import chain

import pandas as pd
from sources.tasks.business_logic.read_mapping_from_postgres import (
    read_mapping_from_postgres,
)
from utils import db_tasks
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def source_data_validate(
    df: pd.DataFrame,
    params: dict,
) -> None:
    """Etape de validation des données source où on applique des règles
    métier scrictes. Par exemple, si un SIRET est malformé c'est qu'on
    pas bien fait notre travail à l'étape de normalisation"""

    # Il nous faut au moins 1 acteur sinon on à un problème avec le source
    # TODO: règles d'anomalies plus avancées (ex: entre 80% et 100% vs. existant)
    if df.empty:
        raise ValueError("Aucune donnée reçue par source_data_normalize")
    log.preview("df avant validation", df)

    # ------------------------------------
    # identifiant_externe
    # Pas de doublons sur identifiant_externe (false=garde first+last)

    # On vérifie que les identifiants uniques sont uniques, on ne se base pas sur
    # l'identifiant externe car il est parfois dupliqués pour des service physique et
    # en ligne
    dups = df[df["identifiant_unique"].duplicated(keep=False)]
    if not dups.empty:
        log.preview("Doublons sur identifiant_unique", dups)
        raise ValueError("Doublons sur identifiant_unique")

    # ------------------------------------
    # acteur_type_code
    df_acteurtype_code = set(df["acteur_type_code"].unique())
    db_acteurtype_code = set(
        db_tasks.read_data_from_postgres(table_name="qfdmo_acteurtype")["code"]
    )
    invalid_acteurtype_codes = df_acteurtype_code - db_acteurtype_code
    if invalid_acteurtype_codes:
        raise ValueError(
            f"acteur_type_code: codes pas dans DB: {invalid_acteurtype_codes}"
        )

    # ------------------------------------
    # source_code
    df_source_code = set(df["source_code"].unique())
    db_source_code = set(
        db_tasks.read_data_from_postgres(table_name="qfdmo_source")["code"]
    )
    invalid_source_codes = df_source_code - db_source_code
    if invalid_source_codes:
        raise ValueError(f"source_code: codes pas dans DB: {invalid_source_codes}")

    # ------------------------------------
    # product_mapping
    # - les valeur du mapping des produit peuvent-être des listes vides quand aucun
    #   produit n'est à associer
    product_mapping = params.get("product_mapping", {})
    souscats_codes_to_ids = read_mapping_from_postgres(
        table_name="qfdmo_souscategorieobjet"
    )
    codes_db = set(souscats_codes_to_ids.keys())
    codes_mapping = set(
        chain.from_iterable(
            x if isinstance(x, list) else [x] for x in product_mapping.values()
        )
    )
    codes_invalid = codes_mapping - codes_db
    if codes_invalid:
        raise ValueError(f"product_mapping: codes pas dans DB: {codes_invalid}")

    # ------------------------------------
    # vérification des codes des acteurservices
    df_acteurservice_code = set(
        chain.from_iterable(
            x if isinstance(x, list) else [x] for x in df["acteurservice_codes"]
        )
    )
    db_acteurservice_code = set(
        db_tasks.read_data_from_postgres(table_name="qfdmo_acteurservice")["code"]
    )
    invalid_acteurservice_codes = df_acteurservice_code - db_acteurservice_code
    if invalid_acteurservice_codes:
        raise ValueError(
            f"acteurservice_codes: codes pas dans DB: {invalid_acteurservice_codes}"
        )

    # ------------------------------------
    # vérification des codes des labels
    df_label_code = set(
        chain.from_iterable(
            x if isinstance(x, list) else [x] for x in df["label_codes"]
        )
    )
    db_label_code = set(
        db_tasks.read_data_from_postgres(table_name="qfdmo_labelqualite")["code"]
    )
    invalid_label_codes = df_label_code - db_label_code
    if invalid_label_codes:
        raise ValueError(f"label_codes: codes pas dans DB: {invalid_label_codes}")

    # ------------------------------------
    # vérification des codes des labels
    df_sscat_code = set(
        chain.from_iterable(
            x if isinstance(x, list) else [x] for x in df["souscategorie_codes"]
        )
    )
    db_sscat_code = set(
        db_tasks.read_data_from_postgres(table_name="qfdmo_souscategorieobjet")["code"]
    )
    invalid_sscat_codes = df_sscat_code - db_sscat_code
    if invalid_sscat_codes:
        raise ValueError(f"sscat_codes: codes pas dans DB: {invalid_sscat_codes}")

    # Le but de la validation n'est pas de modifier les données
    # donc on retourn explicitement None et les tâches suivantes
    # devront se baser sur source_data_normalize

    return None
