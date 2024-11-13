import json
import logging
from datetime import datetime
from typing import Union

import numpy as np
import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy import text
from utils import api_utils, base_utils, mapping_utils, shared_constants
from utils.formatter import format_libelle_to_code

logger = logging.getLogger(__name__)

LABEL_TO_INGNORE = ["non applicable", "na", "n/a", "null", "aucun", "non"]


def fetch_data_from_api(**kwargs):
    params = kwargs["params"]
    api_url = params["endpoint"]
    logger.info(f"Fetching data from API : {api_url}")
    data = api_utils.fetch_data_from_url(api_url)
    logger.info("Fetching data from API done")
    df = pd.DataFrame(data)
    return df


def load_data_from_postgresql(**kwargs):
    pg_hook = PostgresHook(postgres_conn_id="qfdmo_django_db")
    engine = pg_hook.get_sqlalchemy_engine()

    # TODO : check if we need to manage the max id here
    displayedpropositionservice_max_id = engine.execute(
        text("SELECT max(id) FROM qfdmo_displayedpropositionservice")
    ).scalar()

    return {
        "displayedpropositionservice_max_id": displayedpropositionservice_max_id,
    }


def create_proposition_services(**kwargs):
    df = kwargs["ti"].xcom_pull(task_ids="create_actors")["df"]
    data_dict = kwargs["ti"].xcom_pull(task_ids="load_data_from_postgresql")
    displayedpropositionservice_max_id = data_dict["displayedpropositionservice_max_id"]
    rows_dict = {}
    merged_count = 0
    actions_id_by_code = kwargs["ti"].xcom_pull(task_ids="read_action")

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

    return {"df": df_pds, "metadata": metadata}


def create_proposition_services_sous_categories(**kwargs):
    df = kwargs["ti"].xcom_pull(task_ids="create_proposition_services")["df"]
    souscategorieobjet_id_by_code = kwargs["ti"].xcom_pull(
        task_ids="read_souscategorieobjet"
    )
    params = kwargs["params"]
    sous_categories_mapping = params.get("product_mapping", {})
    rows_list = []

    for _, row in df.iterrows():
        sous_categories_value = (
            str(row["sous_categories"]) if row["sous_categories"] else ""
        )
        products = [
            sous_categorie.strip().lower()
            for sous_categorie in sous_categories_value.split("|")
            if sous_categorie.strip()
        ]
        for product in set(products):
            if product in sous_categories_mapping:
                sous_categories_value = sous_categories_mapping[product]
                if sous_categories_value is None:
                    continue
                if isinstance(sous_categories_value, list):
                    for value in sous_categories_value:
                        rows_list.append(
                            {
                                "propositionservice_id": row["id"],
                                "souscategorieobjet_id": souscategorieobjet_id_by_code[
                                    value
                                ],
                                "souscategorie": value,
                            }
                        )
                else:
                    rows_list.append(
                        {
                            "propositionservice_id": row["id"],
                            "souscategorieobjet_id": souscategorieobjet_id_by_code[
                                sous_categories_value
                            ],
                            "souscategorie": sous_categories_value,
                        }
                    )
            else:
                raise Exception(
                    f"Could not find mapping for sous categorie `{product}` in config"
                )

    df_sous_categories = pd.DataFrame(
        rows_list,
        columns=["propositionservice_id", "souscategorieobjet_id", "souscategorie"],
    )

    df_sous_categories.drop_duplicates(
        ["propositionservice_id", "souscategorieobjet_id"], keep="first", inplace=True
    )
    df_sous_categories = df_sous_categories[
        df_sous_categories["souscategorieobjet_id"].notna()
    ]

    return df_sous_categories


def serialize_to_json(**kwargs):
    # Removed acteurs
    df_acteur_to_delete = kwargs["ti"].xcom_pull(task_ids="get_acteur_to_delete")[
        "df_acteur_to_delete"
    ]
    update_actors_columns = ["identifiant_unique", "statut", "cree_le"]
    df_acteur_to_delete["row_updates"] = df_acteur_to_delete[
        update_actors_columns
    ].apply(lambda row: json.dumps(row.to_dict(), default=str), axis=1)
    # Created or updated Acteurs
    df_actors = kwargs["ti"].xcom_pull(task_ids="create_actors")["df"]
    df_ps = kwargs["ti"].xcom_pull(task_ids="create_proposition_services")["df"]
    df_pssc = kwargs["ti"].xcom_pull(
        task_ids="create_proposition_services_sous_categories"
    )
    df_labels = kwargs["ti"].xcom_pull(task_ids="create_labels")
    df_acteur_services = kwargs["ti"].xcom_pull(task_ids="create_acteur_services")
    df_acteur_services = (
        df_acteur_services
        if df_acteur_services is not None
        else pd.DataFrame(columns=["acteur_id", "acteurservice_id"])
    )

    aggregated_pdsc = (
        df_pssc.groupby("propositionservice_id")
        .apply(lambda x: x.to_dict("records") if not x.empty else [])
        .reset_index(name="pds_sous_categories")
    )

    df_pds_joined = pd.merge(
        df_ps,
        aggregated_pdsc,
        how="left",
        left_on="id",
        right_on="propositionservice_id",
    )
    df_pds_joined["propositionservice_id"] = df_pds_joined[
        "propositionservice_id"
    ].astype(str)

    df_pds_joined["pds_sous_categories"] = df_pds_joined["pds_sous_categories"].apply(
        lambda x: x if isinstance(x, list) else []
    )

    df_pds_joined.drop("id", axis=1, inplace=True)

    aggregated_pds = (
        df_pds_joined.groupby("acteur_id")
        .apply(lambda x: x.to_dict("records") if not x.empty else [])
        .reset_index(name="proposition_services")
    )

    aggregated_labels = df_labels.groupby("acteur_id").apply(
        lambda x: x.to_dict("records") if not x.empty else []
    )
    aggregated_labels = (
        pd.DataFrame(columns=["acteur_id", "labels"])
        if aggregated_labels.empty
        else aggregated_labels.reset_index(name="labels")
    )

    aggregated_acteur_services = df_acteur_services.groupby("acteur_id").apply(
        lambda x: x.to_dict("records") if not x.empty else []
    )
    aggregated_acteur_services = (
        pd.DataFrame(columns=["acteur_id", "acteur_services"])
        if aggregated_acteur_services.empty
        else aggregated_acteur_services.reset_index(name="acteur_services")
    )

    df_joined_with_pds = pd.merge(
        df_actors,
        aggregated_pds,
        how="left",
        left_on="identifiant_unique",
        right_on="acteur_id",
    )

    df_joined_with_labels = pd.merge(
        df_joined_with_pds,
        aggregated_labels,
        how="left",
        left_on="acteur_id",
        right_on="acteur_id",
    )

    df_joined = pd.merge(
        df_joined_with_labels,
        aggregated_acteur_services,
        how="left",
        left_on="acteur_id",
        right_on="acteur_id",
    )

    df_joined["proposition_services"] = df_joined["proposition_services"].apply(
        lambda x: x if isinstance(x, list) else []
    )

    df_joined.loc[
        df_joined["proposition_services"].apply(lambda x: x == []), "status"
    ] = "SUPPRIME"

    df_joined.drop("acteur_id", axis=1, inplace=True)

    df_joined = df_joined.where(pd.notna(df_joined), None)

    df_joined["row_updates"] = df_joined.apply(
        lambda row: json.dumps(row.to_dict(), default=str), axis=1
    )
    df_joined.drop_duplicates("identifiant_unique", keep="first", inplace=True)

    return {"all": {"df": df_joined}, "to_disable": {"df": df_acteur_to_delete}}


def read_acteur(**kwargs):
    source_code = kwargs["params"].get("source_code", None)
    df_data_from_api = kwargs["ti"].xcom_pull(task_ids="fetch_data_from_api")
    sources_id_by_code = kwargs["ti"].xcom_pull(task_ids="read_source")

    if source_code is None and "ecoorganisme" not in df_data_from_api.columns:
        raise ValueError(
            "No source code provided and no `ecoorganisme` column in the data"
        )
    if source_code:
        unique_source_ids = [sources_id_by_code[source_code]]
    else:
        df_data_from_api["source_id"] = df_data_from_api["ecoorganisme"].map(
            sources_id_by_code
        )
        unique_source_ids = df_data_from_api["source_id"].unique()

    pg_hook = PostgresHook(postgres_conn_id="qfdmo_django_db")
    engine = pg_hook.get_sqlalchemy_engine()
    joined_source_ids = ",".join([f"'{source_id}'" for source_id in unique_source_ids])
    query = f"SELECT * FROM qfdmo_acteur WHERE source_id IN ({joined_source_ids})"

    df_acteur = pd.read_sql_query(query, engine)

    return df_acteur


def insert_dagrun_and_process_df(df_acteur_updates, metadata, dag_name, run_name):
    if df_acteur_updates.empty:
        return
    pg_hook = PostgresHook(postgres_conn_id="qfdmo_django_db")
    engine = pg_hook.get_sqlalchemy_engine()
    current_date = datetime.now()

    with engine.connect() as conn:
        # Insert a new dagrun
        result = conn.execute(
            """
            INSERT INTO qfdmo_dagrun
            (dag_id, run_id, status, meta_data, created_date, updated_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING ID;
        """,
            (
                dag_name,
                run_name,
                "TO_VALIDATE",
                json.dumps(metadata),
                current_date,
                current_date,
            ),
        )
        dag_run_id = result.fetchone()[0]

    # Insert dag_run_change
    df_acteur_updates["change_type"] = df_acteur_updates["event"]
    df_acteur_updates["dag_run_id"] = dag_run_id
    df_acteur_updates["status"] = shared_constants.TO_VALIDATE
    df_acteur_updates[["row_updates", "dag_run_id", "change_type", "status"]].to_sql(
        "qfdmo_dagrunchange",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )


def write_to_dagruns(**kwargs):
    dag_name = kwargs["dag"].dag_display_name or kwargs["dag"].dag_id
    run_id = kwargs["run_id"]
    dfs = kwargs["ti"].xcom_pull(task_ids="serialize_to_json")
    metadata_actors = (
        kwargs["ti"]
        .xcom_pull(task_ids="create_actors", key="return_value", default={})
        .get("metadata", {})
    )
    metadata_acteur_to_delete = (
        kwargs["ti"]
        .xcom_pull(task_ids="get_acteur_to_delete", key="return_value", default={})
        .get("metadata", {})
    )
    metadata_pds = (
        kwargs["ti"]
        .xcom_pull(
            task_ids="create_proposition_services", key="return_value", default={}
        )
        .get("metadata", {})
    )

    metadata = {**metadata_actors, **metadata_acteur_to_delete, **metadata_pds}

    for key, data in dfs.items():
        # TODO dag_id
        dag_name_suffixed = (
            dag_name if key == "all" else f"{dag_name} - {key.replace('_', ' ')}"
        )
        run_name = run_id.replace("__", " - ")
        df = data["df"]
        metadata.update(data.get("metadata", {}))
        insert_dagrun_and_process_df(df, metadata, dag_name_suffixed, run_name)


def _force_column_value(
    df_column: pd.Series,
    values_mapping: dict,
    default_value: Union[str, bool, None] = None,
) -> pd.Series:
    # set to default value if column is not one of keys or values in values_mapping
    return (
        df_column.str.strip()
        .str.lower()
        .replace(values_mapping)
        .apply(lambda x: (default_value if x not in values_mapping.values() else x))
    )


def cast_eo_boolean_or_string_to_boolean(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower().strip() == "oui"
    return False


def merge_produits_accepter(group):
    produits_sets = set()
    for produits in group:
        produits_sets.update([produit.strip() for produit in produits.split("|")])
    return "|".join(sorted(produits_sets))


def merge_duplicates(
    df, group_column="identifiant_unique", merge_column="produitsdechets_acceptes"
):

    df_duplicates = df[df.duplicated(group_column, keep=False)]
    df_non_duplicates = df[~df.duplicated(group_column, keep=False)]

    df_merged_duplicates = (
        df_duplicates.groupby(group_column)
        .agg(
            {
                **{
                    col: "first"
                    for col in df.columns
                    if col != merge_column and col != group_column
                },
                merge_column: merge_produits_accepter,
            }
        )
        .reset_index()
    )

    # Concatenate the non-duplicates and merged duplicates
    df_final = pd.concat([df_non_duplicates, df_merged_duplicates], ignore_index=True)

    return df_final


def create_actors(**kwargs):
    df = kwargs["ti"].xcom_pull(task_ids="fetch_data_from_api")
    acteurtype_id_by_code = kwargs["ti"].xcom_pull(task_ids="read_acteurtype")
    sources_id_by_code = kwargs["ti"].xcom_pull(task_ids="read_source")
    df_acteurs = kwargs["ti"].xcom_pull(task_ids="read_acteur")

    params = kwargs["params"]
    source_code = params.get("source_code")
    label_bonus_reparation = params.get("label_bonus_reparation")
    column_mapping = params.get("column_mapping", {})
    column_to_drop = params.get("column_to_drop", [])
    columns_to_add_by_default = params.get("columns_to_add_by_default", {})
    combine_columns_categories = params.get("combine_columns_categories")

    if params.get("merge_duplicated_acteurs"):
        df = merge_duplicates(
            df,
            group_column="id_point_apport_ou_reparation",
            merge_column="produitsdechets_acceptes",
        )

    for k, val in columns_to_add_by_default.items():
        df[k] = val

    # Supprimer les acteurs qui ne propose qu'un service à domicile
    if "service_a_domicile" in df.columns:
        df.loc[
            df["service_a_domicile"] == "service à domicile uniquement", "statut"
        ] = "SUPPRIME"

    # filtre des service à domicile uniquement
    if "service_a_domicile" in df.columns:
        df = df[df["service_a_domicile"].str.lower() != "oui exclusivement"]

    # intersection of columns in df and column_to_drop
    column_to_drop = list(set(column_to_drop) & set(df.columns))
    df = df.drop(column_to_drop, axis=1)

    if combine_columns_categories:
        df["produitsdechets_acceptes"] = df.apply(
            lambda row: mapping_utils.combine_categories(
                row, combine_columns_categories
            ),
            axis=1,
        )
    if source_code:
        df["source_id"] = sources_id_by_code[source_code]

    # TODO Plutôt se baser sur le nom de la colonne cible plutôt que sur le nom de la
    # colonne source
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns and new_col:
            if new_col == "identifiant_externe":

                # TODO: simplifier cette partie de code quite à faire des migrations
                if "nom_de_lorganisme" in df.columns:
                    df[old_col] = df[old_col].fillna(
                        df["nom_de_lorganisme"]
                        .str.replace("-", "")
                        .str.replace(" ", "_")
                        .str.replace("__", "_")
                    )
                # TODO: raise si l'identifiant unique n'est pas unique
                df["identifiant_externe"] = df[old_col].astype(str)

            elif new_col == "statut":
                df[new_col] = df[old_col].map({1: "ACTIF", 0: "SUPPRIME"})
            elif new_col == "acteur_type_id":
                df[new_col] = df[old_col].apply(
                    lambda x: mapping_utils.transform_acteur_type_id(
                        x, acteurtype_id_by_code=acteurtype_id_by_code
                    )
                )
            elif new_col == "source_id":
                df[new_col] = df[old_col].map(sources_id_by_code)
            # here we keep the condition on old_col
            elif old_col == "adresse_format_ban":
                df[["adresse", "code_postal", "ville"]] = df.apply(
                    base_utils.get_address, axis=1
                )
            elif new_col == "public_accueilli":
                df[new_col] = _force_column_value(
                    df[old_col],
                    {
                        "particuliers et professionnels": (
                            "Particuliers et professionnels"
                        ),
                        "professionnels": "Professionnels",
                        "particuliers": "Particuliers",
                        "aucun": "Aucun",
                    },
                )
                df["statut"] = df["public_accueilli"].apply(
                    lambda x: "SUPPRIME" if x == "Professionnels" else "ACTIF"
                )
            elif new_col in ["uniquement_sur_rdv", "exclusivite_de_reprisereparation"]:
                df[new_col] = df[old_col].apply(cast_eo_boolean_or_string_to_boolean)
            elif new_col == "reprise":
                df[new_col] = _force_column_value(
                    df[old_col],
                    {
                        "1 pour 0": "1 pour 0",
                        "1 pour 1": "1 pour 1",
                        "non": "1 pour 0",
                        "oui": "1 pour 1",
                    },
                )
            elif new_col == "labels_etou_bonus" and label_bonus_reparation:
                df[new_col] = df[old_col].apply(
                    lambda x: x.replace(
                        "Agréé Bonus Réparation", label_bonus_reparation
                    )
                )
            elif new_col == "url":
                df[new_col] = df[old_col].apply(mapping_utils.prefix_url)

            else:
                df[new_col] = df[old_col]

    if "latitude" in df.columns and "longitude" in df.columns:
        df["latitude"] = df["latitude"].apply(mapping_utils.parse_float)
        df["longitude"] = df["longitude"].apply(mapping_utils.parse_float)
        df["location"] = df.apply(
            lambda row: base_utils.transform_location(
                row["longitude"], row["latitude"]
            ),
            axis=1,
        )

    df["identifiant_unique"] = df.apply(
        lambda x: mapping_utils.create_identifiant_unique(x, source_name=source_code),
        axis=1,
    )

    # On garde le cree_le de qfdmo_acteur
    df.drop(columns=["cree_le"], inplace=True, errors="ignore")
    df = df.merge(
        df_acteurs[["identifiant_unique", "cree_le"]],
        on="identifiant_unique",
        how="left",
    )
    df["cree_le"] = df["cree_le"].fillna(datetime.now())

    # On met à jour le modifie_le de qfdmo_acteur
    df["modifie_le"] = datetime.now()

    if "siret" in df.columns:
        df["siret"] = df["siret"].apply(mapping_utils.process_siret)

    if "telephone" in df.columns and "code_postal" in df.columns:
        df["telephone"] = df.apply(
            lambda row: pd.Series(
                mapping_utils.process_phone_number(row["telephone"], row["code_postal"])
            ),
            axis=1,
        )

    if "code_postal" in df.columns:
        # cast en str et ajout de 0 si le code postal est inférieur à 10000
        df["code_postal"] = df["code_postal"].apply(
            lambda x: f"0{x}" if x and len(str(x)) == 4 else str(x)
        )

    df = df.replace({np.nan: None})

    duplicates_mask = df.duplicated("identifiant_unique", keep=False)
    duplicate_ids = df.loc[duplicates_mask, "identifiant_unique"].unique()
    number_of_duplicates = len(duplicate_ids)

    metadata = {
        "number_of_duplicates": number_of_duplicates,
        "duplicate_ids": list(duplicate_ids),
        "added_rows": len(df),
    }

    df = df.drop_duplicates(subset="identifiant_unique", keep="first")
    df["event"] = "CREATE"
    return {
        "df": df,
        "metadata": metadata,
    }


def get_acteur_to_delete(**kwargs):
    df_acteurs_for_source = kwargs["ti"].xcom_pull(task_ids="create_actors")["df"]
    df_acteurs_from_db = kwargs["ti"].xcom_pull(task_ids="read_acteur")

    df_acteurs_from_db_actifs = df_acteurs_from_db[
        df_acteurs_from_db["statut"] == "ACTIF"
    ]

    df_acteur_to_delete = df_acteurs_from_db_actifs[
        ~df_acteurs_from_db_actifs["identifiant_unique"].isin(
            df_acteurs_for_source["identifiant_unique"]
        )
    ][["identifiant_unique", "cree_le", "modifie_le"]]

    df_acteur_to_delete["statut"] = "SUPPRIME"
    df_acteur_to_delete["event"] = "UPDATE_ACTOR"

    return {
        "metadata": {"number_of_removed_actors": len(df_acteur_to_delete)},
        "df_acteur_to_delete": df_acteur_to_delete,
    }


def create_labels(**kwargs):
    labelqualite_id_by_code = kwargs["ti"].xcom_pull(task_ids="read_labelqualite")
    acteurtype_id_by_code = kwargs["ti"].xcom_pull(task_ids="read_acteurtype")
    df_actors = kwargs["ti"].xcom_pull(task_ids="create_actors")["df"]

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
            if label_ou_bonus in LABEL_TO_INGNORE:
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


def create_acteur_services(**kwargs):
    acteurservice_id_by_code = kwargs["ti"].xcom_pull(task_ids="read_acteurservice")
    df_actors = kwargs["ti"].xcom_pull(task_ids="create_actors")["df"]

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
