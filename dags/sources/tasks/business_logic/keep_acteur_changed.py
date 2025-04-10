import logging

import pandas as pd
from sources.tasks.airflow_logic.config_management import DAGConfig
from sources.tasks.transform.transform_df import compute_identifiant_unique
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def is_identique_row(row_source, row_db, columns_to_compare):
    is_identique = True
    for column in columns_to_compare - {"identifiant_unique"}:
        if column == "proposition_service_codes":
            # on trie la list de dict par la clé action
            row_source[column] = sorted(row_source[column], key=lambda x: x["action"])
            row_db[column] = sorted(row_db[column], key=lambda x: x["action"])
            # on trie les sous_categories dans chaque dict
            for item in row_source[column]:
                item["sous_categories"] = sorted(item["sous_categories"])
            for item in row_db[column]:
                item["sous_categories"] = sorted(item["sous_categories"])
            if row_source[column] != row_db[column]:
                is_identique = False
                break
        elif isinstance(row_source[column], list) and isinstance(row_db[column], list):
            if sorted(row_source[column]) != sorted(row_db[column]):
                is_identique = False
                break
        elif row_source[column] != row_db[column]:
            is_identique = False
            break
    return is_identique


def retrieve_identifiant_unique_from_existing_acteur(
    df_normalized: pd.DataFrame, df_acteur_from_db: pd.DataFrame
):
    if df_normalized.empty or df_acteur_from_db.empty:
        return df_normalized, df_acteur_from_db

    # Adding identifiant column to compare using identifiant_externe and source_code
    # instead of identifiant_unique (for the usecase of external_ids were updated)
    print("df_normalized", df_normalized)
    df_normalized["identifiant"] = df_normalized.apply(
        lambda row: compute_identifiant_unique(
            row["identifiant_externe"], row["source_code"], row["acteur_type_code"]
        ),
        axis=1,
    )
    df_acteur_from_db["identifiant"] = df_acteur_from_db.apply(
        lambda row: compute_identifiant_unique(
            row["identifiant_externe"], row["source_code"], row["acteur_type_code"]
        ),
        axis=1,
    )

    # Replace identifiant_unique (from source) by identifiant (from db) for acteur
    # which doesn't have corelation between source, external_id and identifiant_unique
    df_normalized.set_index("identifiant", inplace=True)
    df_acteur_from_db.set_index("identifiant", inplace=True)
    df_normalized["identifiant_unique"] = df_normalized.index.map(
        lambda x: (
            df_acteur_from_db.loc[x, "identifiant_unique"]
            if x in df_acteur_from_db.index
            else df_normalized.loc[x, "identifiant_unique"]
        )
    )

    # Cleanup
    df_normalized.reset_index(inplace=True)
    df_acteur_from_db.reset_index(inplace=True)
    df_normalized.drop(columns=["identifiant"], inplace=True)
    df_acteur_from_db.drop(columns=["identifiant"], inplace=True)

    return df_normalized, df_acteur_from_db


def keep_acteur_changed(
    df_normalized: pd.DataFrame, df_acteur_from_db: pd.DataFrame, dag_config: DAGConfig
):
    if df_acteur_from_db.empty:
        return {
            "df_acteur": df_normalized,
            "df_acteur_from_db": df_acteur_from_db,
        }

    df_normalized, df_acteur_from_db = retrieve_identifiant_unique_from_existing_acteur(
        df_normalized, df_acteur_from_db
    )

    columns_to_compare = (
        dag_config.get_expected_columns()
        - {
            "location",
            "sous_categorie_codes",
            "action_codes",
        }
        - {"cree_le"}
    )

    # grouper par identifiant_unique et comparer les colonnes
    # si les colonnes sont identiques, on collecte l'identifiant_unique
    identifiant_uniques_from_source = df_normalized["identifiant_unique"].tolist()
    identifiant_uniques_from_db = df_acteur_from_db["identifiant_unique"].tolist()
    df_updated_from_db = df_acteur_from_db[list(columns_to_compare)]
    df_from_source = df_normalized[list(columns_to_compare)]
    df_updated_from_db = df_updated_from_db[
        df_updated_from_db["identifiant_unique"].isin(identifiant_uniques_from_source)
    ]
    df_from_source = df_from_source[
        df_from_source["identifiant_unique"].isin(identifiant_uniques_from_db)
    ]

    df_from_source = df_from_source.set_index("identifiant_unique")
    df_updated_from_db = df_updated_from_db.set_index("identifiant_unique")
    log.preview("df_from_source identifiant_unique identique", df_from_source)
    log.preview("df_from_db identifiant_unique identique", df_updated_from_db)

    noupdate_identifiant_uniques = []
    for index, row_source in df_from_source.iterrows():
        row_source = row_source.to_dict()
        row_db = df_updated_from_db.loc[index]
        row_db = row_db.to_dict()
        if is_identique_row(row_source, row_db, columns_to_compare):
            noupdate_identifiant_uniques.append(index)
    log.preview("identifiant_uniques", noupdate_identifiant_uniques)

    df_normalized = df_normalized[
        ~df_normalized["identifiant_unique"].isin(noupdate_identifiant_uniques)
    ]
    df_acteur_from_db = df_acteur_from_db[
        ~df_acteur_from_db["identifiant_unique"].isin(noupdate_identifiant_uniques)
    ]

    log.preview("df_normalized après suppression", df_normalized)
    return {
        "df_acteur": df_normalized,
        "df_acteur_from_db": df_acteur_from_db,
    }
