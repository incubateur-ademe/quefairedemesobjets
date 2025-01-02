import logging

import pandas as pd
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def propose_services(
    df: pd.DataFrame,
    displayedpropositionservice_max_id: int,
    actions_id_by_code: dict,
) -> dict:
    merged_count = 0
    rows_list = []

    for _, row in df.iterrows():
        for action_code in row["action_codes"]:
            rows_list.append(
                {
                    "action_id": actions_id_by_code[action_code],
                    "acteur_id": row["identifiant_unique"],
                    "action": action_code,
                    "sous_categories": row["souscategorie_codes"],
                }
            )

    df_pds = pd.DataFrame(rows_list)
    if df_pds.empty:
        raise ValueError("df_pds est vide")
    if indexes := range(
        displayedpropositionservice_max_id,
        displayedpropositionservice_max_id + len(df_pds),
    ):
        df_pds["id"] = indexes
    metadata = {
        "number_of_merged_actors": merged_count,
        "number_of_propositionservices": len(df_pds),
    }
    log.preview("df_pds retournée par la tâche", df_pds)

    return {"df": df_pds, "metadata": metadata}
