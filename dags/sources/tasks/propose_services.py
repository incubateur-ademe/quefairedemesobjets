import logging

import numpy as np
import pandas as pd
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def propose_services_task(**kwargs) -> dict:
    df = kwargs["ti"].xcom_pull(task_ids="propose_acteur_changes")["df"]
    data_dict = kwargs["ti"].xcom_pull(task_ids="db_read_propositions_max_id")
    displayedpropositionservice_max_id = data_dict["displayedpropositionservice_max_id"]
    actions_id_by_code = kwargs["ti"].xcom_pull(task_ids="db_read_action")
    return propose_services(
        df=df,
        displayedpropositionservice_max_id=displayedpropositionservice_max_id,
        actions_id_by_code=actions_id_by_code,
    )


def propose_services(
    df: pd.DataFrame,
    displayedpropositionservice_max_id: int,
    actions_id_by_code: dict,
) -> dict:
    rows_dict = {}
    merged_count = 0

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

    df_pds = pd.DataFrame(rows_list)
    if df_pds.empty:
        raise ValueError("df_pds est vide")
    if "sous_categories" in df_pds.columns:
        df_pds["sous_categories"] = df_pds["sous_categories"].replace(np.nan, None)
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
