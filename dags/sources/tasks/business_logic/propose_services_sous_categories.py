import logging

import pandas as pd
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def propose_services_sous_categories(
    df_ps: pd.DataFrame,
    souscats_id_by_code: dict,
):
    rows_list = []

    log.preview("df_ps", df_ps)
    logger.info(df_ps.head(1).to_dict(orient="records"))
    log.preview("souscats_id_by_code", souscats_id_by_code)

    for _, row in df_ps.iterrows():
        for sscat_code in set(row["sous_categories"]):
            rows_list.append(
                {
                    "propositionservice_id": row["id"],
                    "souscategorieobjet_id": souscats_id_by_code[sscat_code],
                    "souscategorie": sscat_code,
                }
            )

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
