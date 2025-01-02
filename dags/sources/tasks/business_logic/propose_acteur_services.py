import pandas as pd


def propose_acteur_services(df_acteur: pd.DataFrame, acteurservice_id_by_code: dict):

    acteur_acteurservice_list = []
    for _, acteur in df_acteur.iterrows():
        for acteurservice_code in acteur["acteurservice_codes"]:
            acteur_acteurservice_list.append(
                {
                    "acteur_id": acteur["identifiant_unique"],
                    "acteurservice_id": acteurservice_id_by_code[acteurservice_code],
                }
            )

    df_acteur_services = pd.DataFrame(
        acteur_acteurservice_list,
        columns=["acteur_id", "acteurservice_id"],
    )
    return df_acteur_services
