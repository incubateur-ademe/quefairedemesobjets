import logging

import pandas as pd

logger = logging.getLogger(__name__)


def propose_acteur_to_delete(
    df_acteurs_for_source: pd.DataFrame,
    df_acteurs_from_db: pd.DataFrame,
):

    df_acteurs_from_db_actifs = df_acteurs_from_db[
        df_acteurs_from_db["statut"] == "ACTIF"
    ]

    df_acteur_to_delete = df_acteurs_from_db_actifs[
        ~df_acteurs_from_db_actifs["identifiant_unique"].isin(
            df_acteurs_for_source["identifiant_unique"]
        )
    ][["identifiant_unique", "cree_le", "modifie_le"]]

    df_acteur_to_delete["statut"] = "SUPPRIME"
    df_acteur_to_delete["event"] = "UPDATE_ACTOR"

    return {
        "metadata": {"number_of_removed_actors": len(df_acteur_to_delete)},
        "df_acteur_to_delete": df_acteur_to_delete,
    }
