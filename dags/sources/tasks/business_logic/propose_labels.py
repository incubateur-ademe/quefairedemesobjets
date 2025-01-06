import pandas as pd

LABEL_TO_IGNORE = ["non applicable", "na", "n/a", "null", "aucun", "non"]
ACTEUR_TYPE_ESS = "ess"


def propose_labels(
    df_acteur: pd.DataFrame,
    labelqualite_id_by_code: dict,
) -> pd.DataFrame:

    rows_list = []
    for _, row in df_acteur.iterrows():

        for label_ou_bonus in row["label_codes"]:
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
