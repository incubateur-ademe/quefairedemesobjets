import logging

import pandas as pd
from sources.tasks.airflow_logic.config_management import DAGConfig
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def is_identique_row(row_source, row_db, columns_to_compare):
    is_identique = True
    for column in columns_to_compare - {"identifiant_unique"}:
        if column == "proposition_services_codes":
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


def keep_acteur_changed(
    df_normalized: pd.DataFrame, df_acteur_from_db: pd.DataFrame, dag_config: DAGConfig
):
    columns_to_compare = (
        dag_config.get_expected_columns()
        - {
            "location",
            "souscategorie_codes",
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
