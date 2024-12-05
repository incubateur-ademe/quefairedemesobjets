import logging
from datetime import datetime

import numpy as np
import pandas as pd
from sources.tasks.transform.transform_df import clean_phone_number
from utils.base_utils import transform_location
from utils.mapping_utils import parse_float

logger = logging.getLogger(__name__)


def propose_acteur_changes(
    df: pd.DataFrame,
    df_acteurs: pd.DataFrame,
    column_to_drop: list = [],
):
    # Supprimer les acteurs qui ne propose qu'un service à domicile
    if "service_a_domicile" in df.columns:
        df.loc[
            df["service_a_domicile"] == "service à domicile uniquement", "statut"
        ] = "SUPPRIME"

    # filtre des service à domicile uniquement
    if "service_a_domicile" in df.columns:
        df = df[df["service_a_domicile"].str.lower() != "oui exclusivement"]

    # TODO: à déplacer dans la source_data_normalize
    # intersection of columns in df and column_to_drop
    column_to_drop = list(set(column_to_drop) & set(df.columns))
    df = df.drop(column_to_drop, axis=1)

    if "latitude" in df.columns and "longitude" in df.columns:
        df["latitude"] = df["latitude"].apply(parse_float)
        df["longitude"] = df["longitude"].apply(parse_float)
        df["location"] = df.apply(
            lambda row: transform_location(row["longitude"], row["latitude"]),
            axis=1,
        )

    # On garde le cree_le de qfdmo_acteur
    df.drop(columns=["cree_le"], inplace=True, errors="ignore")
    df = df.merge(
        df_acteurs[["identifiant_unique", "cree_le"]],
        on="identifiant_unique",
        how="left",
    )
    df["cree_le"] = df["cree_le"].fillna(datetime.now())

    # On met à jour le modifie_le de qfdmo_acteur
    df["modifie_le"] = datetime.now()

    # TODO : à déplacer dans la source_data_normalize
    if "telephone" in df.columns and "code_postal" in df.columns:
        df["telephone"] = df.apply(
            lambda row: pd.Series(
                clean_phone_number(row["telephone"], row["code_postal"])
            ),
            axis=1,
        )

    # TODO : à déplacer dans la source_data_normalize
    if "code_postal" in df.columns:
        # cast en str et ajout de 0 si le code postal est inférieur à 10000
        df["code_postal"] = df["code_postal"].apply(
            lambda x: f"0{x}" if x and len(str(x)) == 4 else str(x)
        )

    df = df.replace({np.nan: None})

    duplicates_mask = df.duplicated("identifiant_unique", keep=False)
    duplicate_ids = df.loc[duplicates_mask, "identifiant_unique"].unique()
    number_of_duplicates = len(duplicate_ids)

    metadata = {
        "number_of_duplicates": number_of_duplicates,
        "duplicate_ids": list(duplicate_ids),
        "acteurs_to_add_or_update": len(df),
    }

    df = df.drop_duplicates(subset="identifiant_unique", keep="first")
    df["event"] = "CREATE"
    return {
        "df": df,
        "metadata": metadata,
    }
