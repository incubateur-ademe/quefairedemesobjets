import json
import logging

import numpy as np
import pandas as pd
from sources.config import shared_constants as constants
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def db_data_prepare(
    df_acteur: pd.DataFrame,
    df_acteur_from_db: pd.DataFrame,
):
    # Before apply json.dumps, replace NaN by None
    df_acteur = df_acteur.replace({np.nan: None})
    df_acteur_from_db = df_acteur_from_db.replace({np.nan: None})

    # Create the "contexte" column which contain a json version of the df_acteur_from_db
    # NaN should be replaced by None to be able to convert the dataframe to db
    # compatible json
    df_acteur_from_db["contexte"] = df_acteur_from_db.apply(
        lambda row: json.dumps(row.to_dict(), default=str), axis=1
    )

    df_acteur_from_db_actifs = df_acteur_from_db[
        df_acteur_from_db["statut"] == constants.ACTEUR_ACTIF
    ]

    df_acteur_to_delete = df_acteur_from_db_actifs[
        ~df_acteur_from_db_actifs["id"].isin(df_acteur["id"])
    ][["id"]]

    df_acteur_to_delete["statut"] = "SUPPRIME"

    df_acteur_to_delete["suggestion"] = df_acteur_to_delete[["id", "statut"]].apply(
        lambda row: json.dumps(row.to_dict(), default=str), axis=1
    )

    df_acteur_to_delete = df_acteur_to_delete.merge(
        df_acteur_from_db[["id", "contexte"]],
        on="id",
        how="inner",
    )

    # FIXME : à faire avant dans la normalisation des données
    # Inactivate acteur if propositions_services is empty
    df_acteur.loc[
        df_acteur["proposition_service_codes"].apply(lambda x: x == []), "statut"
    ] = "INACTIF"

    df_acteur["suggestion"] = df_acteur.apply(
        lambda row: json.dumps(row.to_dict(), default=str), axis=1
    )

    df_acteur_to_create = df_acteur[
        ~df_acteur["id"].isin(df_acteur_from_db["id"])
    ].copy()
    df_acteur_to_create["contexte"] = None

    df_acteur_to_update = df_acteur[
        df_acteur["id"].isin(df_acteur_from_db["id"])
    ].copy()
    df_acteur_to_update = df_acteur_to_update.merge(
        df_acteur_from_db[["id", "contexte"]],
        on="id",
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
