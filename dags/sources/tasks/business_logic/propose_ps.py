import logging

import numpy as np
import pandas as pd
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def propose_ps(
    df: pd.DataFrame,
    dps_max_id: int,
    actions_id_by_code: dict,
) -> dict:
    rows_dict = {}
    merged_count = 0

    # TODO : à déplacer dans la source_data_normalize
    conditions = [
        ("point_dapport_de_service_reparation", "reparer"),
        (
            "point_dapport_pour_reemploi",
            "donner",
        ),
        ("point_de_reparation", "reparer"),
        (
            "point_de_collecte_ou_de_reprise_des_dechets",
            "trier",
        ),
    ]

    for _, row in df.iterrows():
        acteur_id = row["identifiant_unique"]
        # TODO: ne pas gérer la données avec des str |, cinder en liste dès la norma
        sous_categories = row["produitsdechets_acceptes"]

        for condition, action_name in conditions:
            if row.get(condition):
                action_id = actions_id_by_code[action_name]
                key = (action_id, acteur_id)

                if key in rows_dict:
                    if sous_categories not in rows_dict[key]["sous_categories"]:
                        merged_count = +merged_count
                        rows_dict[key]["sous_categories"] += " | " + sous_categories
                else:
                    rows_dict[key] = {
                        "action_id": action_id,
                        "acteur_id": acteur_id,
                        "action": action_name,
                        "sous_categories": sous_categories,
                    }

    rows_list = list(rows_dict.values())

    df_ps = pd.DataFrame(rows_list)
    if df_ps.empty:
        raise ValueError("df_ps est vide")
    if "sous_categories" in df_ps.columns:
        df_ps["sous_categories"] = df_ps["sous_categories"].replace(np.nan, None)
    if indexes := range(
        dps_max_id,
        dps_max_id + len(df_ps),
    ):
        df_ps["id"] = indexes
    metadata = {
        "number_of_merged_actors": merged_count,
        "number_of_propositionservices": len(df_ps),
    }
    log.preview("df_ps retournée par la tâche", df_ps)

    return {"df": df_ps, "metadata": metadata}
