import pandas as pd


def compute_link_tables(
    df_acteur: pd.DataFrame,
    acteurservice_id_by_code: dict,
    labelqualite_id_by_code: dict,
    actions_id_by_code: dict,
    souscats_id_by_code: dict,
    source_id_by_code: dict,
    acteurtype_id_by_code: dict,
) -> pd.DataFrame:

    # FIXME: ajout du controle de la présence des colonnes dand l'action validate data
    # (après la normalisation)

    # Compute qfdmo_acteur_acteurservice
    df_acteur["acteur_services"] = df_acteur.apply(
        lambda row: [
            {
                "acteurservice_id": acteurservice_id_by_code[acteurservice_code],
                "acteur_id": row["identifiant_unique"],
            }
            for acteurservice_code in row["acteurservice_codes"]
        ],
        axis=1,
    )

    # Compute qfdmo_acteur_labelqualite
    df_acteur["labels"] = df_acteur.apply(
        lambda row: [
            {
                "acteur_id": row["identifiant_unique"],
                "labelqualite_id": labelqualite_id_by_code[label_ou_bonus],
            }
            for label_ou_bonus in row["label_codes"]
        ],
        axis=1,
    )

    df_acteur["proposition_services"] = df_acteur.apply(
        lambda row: [
            {
                "acteur_id": row["identifiant_unique"],
                "action_id": actions_id_by_code[action_code],
                "action": action_code,
                "sous_categories": sous_categories,
                "pds_sous_categories": [
                    {
                        "souscategorie": sous_categorie,
                        "souscategorieobjet_id": souscats_id_by_code[sous_categorie],
                    }
                    for sous_categorie in sous_categories
                ],
            }
            for proposition_services_code in row["proposition_services_codes"]
            for action_code, sous_categories in [
                (
                    proposition_services_code["action"],
                    proposition_services_code["sous_categories"],
                )
            ]
        ],
        axis=1,
    )

    # Convertir les codes des sources et des acteur_types en identifiants
    df_acteur["source_id"] = df_acteur["source_code"].map(source_id_by_code)
    df_acteur["acteur_type_id"] = df_acteur["acteur_type_code"].map(
        acteurtype_id_by_code
    )

    return df_acteur
