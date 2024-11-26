import pandas as pd


def propose_acteur_services(df_actors: pd.DataFrame, acteurservice_id_by_code: dict):

    acteurservice_acteurserviceid = {
        "service_de_reparation": acteurservice_id_by_code["service_de_reparation"],
        "structure_de_collecte": acteurservice_id_by_code["structure_de_collecte"],
    }
    acteurservice_eovalues = {
        "service_de_reparation": [
            "point_dapport_de_service_reparation",
            "point_de_reparation",
        ],
        "structure_de_collecte": [
            "point_dapport_pour_reemploi",
            "point_de_collecte_ou_de_reprise_des_dechets",
        ],
    }
    acteur_acteurservice_list = []
    for _, eo_acteur in df_actors.iterrows():
        for acteur_service, eo_values in acteurservice_eovalues.items():
            if any(eo_acteur.get(eo_value) for eo_value in eo_values):
                acteur_acteurservice_list.append(
                    {
                        "acteur_id": eo_acteur["identifiant_unique"],
                        "acteurservice_id": acteurservice_acteurserviceid[
                            acteur_service
                        ],
                    }
                )

    df_acteur_services = pd.DataFrame(
        acteur_acteurservice_list,
        columns=["acteur_id", "acteurservice_id"],
    )
    return df_acteur_services
