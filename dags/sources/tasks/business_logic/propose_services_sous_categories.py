import logging

import pandas as pd
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def propose_services_sous_categories(
    df_ps: pd.DataFrame,
    souscats_id_by_code: dict,
    product_mapping: dict,
):
    rows_list = []

    log.preview("df_ps", df_ps)
    logger.info(df_ps.head(1).to_dict(orient="records"))
    log.preview("souscats_id_by_code", souscats_id_by_code)
    log.preview("product_mapping", product_mapping)

    for _, row in df_ps.iterrows():
        # TODO: à déplacer dans source_data_normalize
        if isinstance(row["sous_categories"], str):
            sous_categories_value = (
                str(row["sous_categories"]) if row["sous_categories"] else ""
            )
            souscats = [
                sous_categorie.strip().lower()
                for sous_categorie in sous_categories_value.split("|")
                if sous_categorie.strip()
            ]
        elif isinstance(row["sous_categories"], list):
            souscats = row["sous_categories"]
        else:
            raise ValueError(
                f"sous_categories: mauvais format {type(row['sous_categories'])}"
            )
        for souscat in set(souscats):
            if souscat in product_mapping:
                sous_categories_value = product_mapping[souscat]
                if isinstance(sous_categories_value, list):
                    for value in sous_categories_value:
                        rows_list.append(
                            {
                                "propositionservice_id": row["id"],
                                "souscategorieobjet_id": souscats_id_by_code[value],
                                "souscategorie": value,
                            }
                        )
                elif isinstance(sous_categories_value, str):
                    rows_list.append(
                        {
                            "propositionservice_id": row["id"],
                            "souscategorieobjet_id": souscats_id_by_code[
                                sous_categories_value
                            ],
                            "souscategorie": sous_categories_value,
                        }
                    )
                else:
                    raise ValueError(
                        f"le type de la Sous categorie `{sous_categories_value}` dans"
                        " la config n'est pas valide"
                    )
            else:
                raise Exception(f"Sous categorie `{souscat}` pas dans la config")

    df_souscats = pd.DataFrame(
        rows_list,
        columns=["propositionservice_id", "souscategorieobjet_id", "souscategorie"],
    )
    log.preview("df_souscats créée par le mapping souscats", df_souscats)
    logger.info(f"# entrées df_souscats avant nettoyage: {len(df_souscats)}")
    df_souscats.drop_duplicates(
        ["propositionservice_id", "souscategorieobjet_id"], keep="first", inplace=True
    )
    logger.info(f"# entrées df_souscats après suppression doublons: {len(df_souscats)}")
    df_souscats = df_souscats[df_souscats["souscategorieobjet_id"].notna()]
    logger.info(f"# entrées df_souscats après nettoyage des vides: {len(df_souscats)}")
    if df_souscats.empty:
        raise ValueError("df_souscats est vide")
    return df_souscats
