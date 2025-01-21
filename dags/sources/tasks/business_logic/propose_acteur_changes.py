import logging
from datetime import datetime

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def propose_acteur_changes(
    df_acteur: pd.DataFrame,
    df_acteur_from_db: pd.DataFrame,
):
    # On garde le cree_le de qfdmo_acteur
    df_acteur.drop(columns=["cree_le"], inplace=True, errors="ignore")
    df_acteur = df_acteur.merge(
        df_acteur_from_db[["identifiant_unique", "cree_le"]],
        on="identifiant_unique",
        how="left",
    )
    df_acteur["cree_le"] = df_acteur["cree_le"].fillna(datetime.now())

    # On met à jour le modifie_le de qfdmo_acteur
    df_acteur["modifie_le"] = datetime.now()

    df_acteur = df_acteur.replace({np.nan: None})

    duplicates_mask = df_acteur.duplicated("identifiant_unique", keep=False)
    duplicate_ids = df_acteur.loc[duplicates_mask, "identifiant_unique"].unique()
    number_of_duplicates = len(duplicate_ids)

    metadata = {
        "number_of_duplicates": number_of_duplicates,
        "duplicate_ids": list(duplicate_ids),
        "acteurs_to_add_or_update": len(df_acteur),
    }

    df_acteur = df_acteur.drop_duplicates(subset="identifiant_unique", keep="first")
    df_acteur["event"] = "CREATE"
    return {
        "df": df_acteur,
        "metadata": metadata,
    }
