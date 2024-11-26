import pandas as pd
from utils.formatter import format_libelle_to_code

LABEL_TO_IGNORE = ["non applicable", "na", "n/a", "null", "aucun", "non"]


def propose_labels(
    df_actors: pd.DataFrame,
    labelqualite_id_by_code: dict,
    acteurtype_id_by_code: dict,
):

    # Get ESS constant values to use in in the loop
    ess_acteur_type_id = acteurtype_id_by_code["ess"]
    ess_label_id = labelqualite_id_by_code["ess"]

    rows_list = []
    for _, row in df_actors.iterrows():

        # Handle special case for ESS
        if row["acteur_type_id"] == ess_acteur_type_id:
            rows_list.append(
                {
                    "acteur_id": row["identifiant_unique"],
                    "labelqualite_id": ess_label_id,
                }
            )

        labels_etou_bonus = row.get("labels_etou_bonus", "")
        if not labels_etou_bonus:
            continue
        for label_ou_bonus in labels_etou_bonus.split("|"):
            label_ou_bonus = format_libelle_to_code(label_ou_bonus)
            if label_ou_bonus in LABEL_TO_IGNORE:
                continue
            if label_ou_bonus not in labelqualite_id_by_code.keys():
                raise ValueError(
                    f"Label ou bonus {label_ou_bonus} not found in database"
                )
            rows_list.append(
                {
                    "acteur_id": row["identifiant_unique"],
                    "labelqualite_id": labelqualite_id_by_code[label_ou_bonus],
                }
            )

    df_labels = pd.DataFrame(rows_list, columns=["acteur_id", "labelqualite_id"])
    df_labels.drop_duplicates(
        ["acteur_id", "labelqualite_id"], keep="first", inplace=True
    )
    return df_labels
