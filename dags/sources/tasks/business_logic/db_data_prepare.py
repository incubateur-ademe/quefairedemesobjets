import json
import logging

import pandas as pd
from sources.config import shared_constants as constants
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def db_data_prepare(
    df_acteur: pd.DataFrame,
    df_acteur_from_db: pd.DataFrame,
):
    # transformer df_acteur_from_db en df [['identifiant_unique', 'contexte']]
    # dans context, on veut la ligne en json
    df_acteur_from_db["contexte"] = df_acteur_from_db.apply(
        lambda row: json.dumps(row.to_dict(), default=str), axis=1
    )

    df_acteur_from_db_actifs = df_acteur_from_db[
        df_acteur_from_db["statut"] == constants.ACTEUR_ACTIF
    ]

    df_acteur_to_delete = df_acteur_from_db_actifs[
        ~df_acteur_from_db_actifs["identifiant_unique"].isin(
            df_acteur["identifiant_unique"]
        )
    ][["identifiant_unique"]]

    df_acteur_to_delete["statut"] = "SUPPRIME"

    df_acteur_to_delete["suggestion"] = df_acteur_to_delete[
        ["identifiant_unique", "statut"]
    ].apply(lambda row: json.dumps(row.to_dict(), default=str), axis=1)

    df_acteur_to_delete = df_acteur_to_delete.merge(
        df_acteur_from_db[["identifiant_unique", "contexte"]],
        on="identifiant_unique",
        how="inner",
    )

    # FIXME : à faire avant dans la normalisation des données
    # Inactivate acteur if propositions_services is empty
    df_acteur.loc[
        df_acteur["proposition_services"].apply(lambda x: x == []), "statut"
    ] = "INACTIF"

    df_acteur["suggestion"] = df_acteur.apply(
        lambda row: json.dumps(row.to_dict(), default=str), axis=1
    )

    df_acteur_to_create = df_acteur[
        ~df_acteur["identifiant_unique"].isin(df_acteur_from_db["identifiant_unique"])
    ].copy()
    df_acteur_to_create["contexte"] = None

    df_acteur_to_update = df_acteur[
        df_acteur["identifiant_unique"].isin(df_acteur_from_db["identifiant_unique"])
    ].copy()
    df_acteur_to_update = df_acteur_to_update.merge(
        df_acteur_from_db[["identifiant_unique", "contexte"]],
        on="identifiant_unique",
        how="left",
    )

    log.preview("df_acteur_to_create", df_acteur_to_create)
    log.preview("df_acteur_to_update", df_acteur_to_update)
    log.preview("df_acteur_to_delete", df_acteur_to_delete)

    return {
        "df_acteur_to_create": df_acteur_to_create,
        "df_acteur_to_update": df_acteur_to_update,
        "df_acteur_to_delete": df_acteur_to_delete,
    }
