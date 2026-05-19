import json
import logging

import numpy as np
import pandas as pd
from sources.tasks.transform.sequence_utils import is_empty_sequence
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def db_data_prepare(
    df_acteur: pd.DataFrame,
    df_acteur_from_db: pd.DataFrame,
):
    from qfdmo.models.acteur import ActeurStatus

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
        df_acteur_from_db["statut"] == ActeurStatus.ACTIF.value
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
        df_acteur["proposition_service_codes"].apply(is_empty_sequence), "statut"
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
        "metadata_to_update": {
            "Nombre d'acteurs à mettre à jour": len(df_acteur_to_update),
        },
        "metadata_to_create": {
            "Nombre d'acteurs à créer": len(df_acteur_to_create),
        },
        "metadata_to_delete": {
            "Nombre d'acteurs à supprimer": len(df_acteur_to_delete),
        },
    }
