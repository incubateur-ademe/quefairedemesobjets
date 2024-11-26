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
    # acteur_type_id
    ids_df = set(df["acteur_type_id"].unique())
    ids_db = set(db_tasks.read_data_from_postgres(table_name="qfdmo_acteurtype")["id"])
    ids_invalid = ids_df - ids_db
    if ids_invalid:
        raise ValueError(f"acteur_type_id: ids pas dans DB: {ids_invalid}")

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
    # produitsdechets_acceptes
    # - les valeurs de produits acceptés doivent être de type string ou list et non
    #   vides
    df_produits_invalid = df[
        ~df["produitsdechets_acceptes"].apply(
            lambda x: isinstance(x, (str, list)) and bool(x)
        )
    ]
    if not df_produits_invalid.empty:
        log.preview("produitsdechets_acceptes invalid", df_produits_invalid)
        raise ValueError("produitsdechets_acceptes invalid")

    # Le but de la validation n'est pas de modifier les données
    # donc on retourn explicitement None et les tâches suivantes
    # devront se baser sur source_data_normalize
    return None
