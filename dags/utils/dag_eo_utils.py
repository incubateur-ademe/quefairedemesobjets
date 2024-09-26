import json
import logging
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook

env = Path(__file__).parent.parent.name
shared_constants = import_module(f"{env}.utils.shared_constants")

logger = logging.getLogger(__name__)

env = Path(__file__).parent.parent.name

utils = import_module(f"{env}.utils.utils")
api_utils = import_module(f"{env}.utils.api_utils")
mapping_utils = import_module(f"{env}.utils.mapping_utils")


def fetch_data_from_api(**kwargs):
    params = kwargs["params"]
    api_url = params["endpoint"]
    logger.info(f"Fetching data from API : {api_url}")
    data = api_utils.fetch_data_from_url(api_url)
    df = pd.DataFrame(data)
    return df


def create_proposition_services(**kwargs):
    df = kwargs["ti"].xcom_pull(task_ids="create_actors")["df"]
    data_dict = kwargs["ti"].xcom_pull(task_ids="load_data_from_postgresql")
    idx_max = data_dict["max_pds_idx"]
    rows_dict = {}
    merged_count = 0
    df_actions = data_dict["actions"]

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
                action_id = mapping_utils.get_id_from_code(action_name, df_actions)
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
    if indexes := range(idx_max, idx_max + len(df_pds)):
        df_pds["id"] = indexes
    metadata = {
        "number_of_merged_actors": merged_count,
        "number_of_propositionservices": len(df_pds),
    }

    return {"df": df_pds, "metadata": metadata}


def create_proposition_services_sous_categories(**kwargs):
    df = kwargs["ti"].xcom_pull(task_ids="create_proposition_services")["df"]
    data_dict = kwargs["ti"].xcom_pull(task_ids="load_data_from_postgresql")
    config = kwargs["ti"].xcom_pull(task_ids="create_actors")["config"]
    df_sous_categories_map = data_dict["sous_categories"]
    params = kwargs["params"]
    mapping_config_key = params.get("mapping_config_key", "sous_categories")
    rows_list = []
    sous_categories = config[mapping_config_key]

    for _, row in df.iterrows():
        sous_categories_value = (
            str(row["sous_categories"]) if row["sous_categories"] else ""
        )
        products = [
            sous_categorie
            for sous_categorie in sous_categories_value.split("|")
            if sous_categorie
        ]
        for product in set(products):
            product_key = product.strip().lower()
            if product_key in sous_categories:
                sous_categories_value = sous_categories[product_key]
                if isinstance(sous_categories_value, list):
                    for value in sous_categories_value:
                        rows_list.append(
                            {
                                "propositionservice_id": row["id"],
                                "souscategorieobjet_id": mapping_utils.get_id_from_code(
                                    value, df_sous_categories_map
                                ),
                                "souscategorie": value,
                            }
                        )
                else:
                    rows_list.append(
                        {
                            "propositionservice_id": row["id"],
                            "souscategorieobjet_id": mapping_utils.get_id_from_code(
                                sous_categories_value, df_sous_categories_map
                            ),
                            "souscategorie": product.strip(),
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
    df_removed_actors = kwargs["ti"].xcom_pull(task_ids="create_actors")[
        "removed_actors"
    ]
    update_actors_columns = ["identifiant_unique", "statut"]
    df_removed_actors["row_updates"] = df_removed_actors[update_actors_columns].apply(
        lambda row: json.dumps(row.to_dict(), default=str), axis=1
    )
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
        else pd.DataFrame(columns=["acteur_id", "acteurservice_id", "acteurservice"])
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

    return {"all": {"df": df_joined}, "to_disable": {"df": df_removed_actors}}


def load_data_from_postgresql(**kwargs):
    pg_hook = PostgresHook(
        postgres_conn_id=utils.get_db_conn_id(__file__, parent_of_parent=True)
    )
    engine = pg_hook.get_sqlalchemy_engine()

    df_acteurtype = pd.read_sql_table("qfdmo_acteurtype", engine)
    df_sources = pd.read_sql_table("qfdmo_source", engine)
    df_actions = pd.read_sql_table("qfdmo_action", engine)
    df_acteur_services = pd.read_sql_table("qfdmo_acteurservice", engine)
    df_sous_categories_objet = pd.read_sql_table("qfdmo_souscategorieobjet", engine)
    df_label = pd.read_sql_table("qfdmo_labelqualite", engine)
    max_id_pds = pd.read_sql_query(
        "SELECT max(id) FROM qfdmo_displayedpropositionservice", engine
    )["max"][0]
    # TODO : ici on rappatrie tous les acteurs, ce serait bien de filtrer par source_id
    # TODO : est-ce qu'on doit lire les acteurs dans qfdmo_displayedacteur ou
    # qfdmo_acteur ?
    df_displayedacteurs = pd.read_sql_table("qfdmo_displayedacteur", engine)

    return {
        "acteurtype": df_acteurtype,
        "sources": df_sources,
        "actions": df_actions,
        "acteur_services": df_acteur_services,
        "max_pds_idx": max_id_pds,
        "sous_categories": df_sous_categories_objet,
        "labels": df_label,
        "displayedacteurs": df_displayedacteurs,
    }


def load_data_from_displayedactor_by_source(source_id):
    pg_hook = PostgresHook(
        postgres_conn_id=utils.get_db_conn_id(__file__, parent_of_parent=True)
    )
    engine = pg_hook.get_sqlalchemy_engine()

    df_displayedactors = pd.read_sql_query(
        f"SELECT identifiant_unique, cree_le, modifie_le "
        f"FROM qfdmo_displayedacteur where statut='ACTIF' "
        f"and source_id={source_id}",
        engine,
    )

    return df_displayedactors


def insert_dagrun_and_process_df(df, metadata, dag_id, run_id):
    pg_hook = PostgresHook(
        postgres_conn_id=utils.get_db_conn_id(__file__, parent_of_parent=True)
    )
    engine = pg_hook.get_sqlalchemy_engine()
    current_date = datetime.now()

    with engine.connect() as conn:
        result = conn.execute(
            """
            INSERT INTO qfdmo_dagrun
            (dag_id, run_id, status, meta_data, created_date, updated_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING ID;
        """,
            (
                dag_id,
                run_id,
                "TO_VALIDATE",
                json.dumps(metadata),
                current_date,
                current_date,
            ),
        )
        dag_run_id = result.fetchone()[0]

    df["change_type"] = df["event"]
    df["dag_run_id"] = dag_run_id
    df["status"] = shared_constants.TO_VALIDATE
    df[["row_updates", "dag_run_id", "change_type", "status"]].to_sql(
        "qfdmo_dagrunchange",
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )


def write_to_dagruns(**kwargs):
    dag_id = kwargs["dag"].dag_id
    run_id = kwargs["run_id"]
    dfs = kwargs["ti"].xcom_pull(task_ids="serialize_to_json")
    metadata_actors = (
        kwargs["ti"]
        .xcom_pull(task_ids="create_actors", key="return_value", default={})
        .get("metadata", {})
    )
    metadata_pds = (
        kwargs["ti"]
        .xcom_pull(
            task_ids="create_proposition_services", key="return_value", default={}
        )
        .get("metadata", {})
    )

    metadata = {}
    if metadata_actors:
        metadata.update(metadata_actors)
    if metadata_pds:
        metadata.update(metadata_pds)

    for key, data in dfs.items():
        dag_id_suffixed = dag_id if key == "all" else f"{dag_id}_{key}"
        df = data["df"]
        metadata.update(data.get("metadata", {}))
        insert_dagrun_and_process_df(df, metadata, dag_id_suffixed, run_id)


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
    data_dict = kwargs["ti"].xcom_pull(task_ids="load_data_from_postgresql")
    df = kwargs["ti"].xcom_pull(task_ids="fetch_data_from_api")
    df_sources = data_dict["sources"]
    df_acteurtype = data_dict["acteurtype"]
    df_displayedacteurs = data_dict["displayedacteurs"]
    config = utils.get_mapping_config()
    params = kwargs["params"]
    reparacteurs = params.get("reparacteurs", False)
    column_mapping = params.get("column_mapping", {})
    column_to_drop = params.get("column_to_drop", [])
    column_to_replace = params.get("default_column_value", {})

    if params.get("multi_ecoorganisme"):
        df = merge_duplicates(
            df,
            group_column="id_point_apport_ou_reparation",
            merge_column="produitsdechets_acceptes",
        )

    # intersection of columns in df and column_to_drop
    column_to_drop = list(set(column_to_drop) & set(df.columns))
    df = df.drop(column_to_drop, axis=1)

    for k, val in column_to_replace.items():
        df[k] = val
    if reparacteurs:
        df = mapping_utils.process_reparacteurs(df, df_sources, df_acteurtype)
    else:
        df = mapping_utils.process_actors(df)

    # By default, all actors are active
    # TODO : manage constant as an enum in config
    df["statut"] = "ACTIF"

    for old_col, new_col in column_mapping.items():
        if old_col in df.columns and new_col:
            if old_col == "id":
                df[new_col] = df["id"].astype(str)
            elif old_col == "is_enabled":
                df[new_col] = df[old_col].map({1: "ACTIF", 0: "SUPPRIME"})
            elif old_col == "type_de_point_de_collecte":
                df[new_col] = df[old_col].apply(
                    lambda x: mapping_utils.transform_acteur_type_id(
                        x, df_acteurtype=df_acteurtype
                    )
                )
            elif old_col == "ecoorganisme":
                df[new_col] = df[old_col].apply(
                    lambda x: mapping_utils.get_id_from_code(x, df_sources)
                )
            elif old_col == "adresse_format_ban":
                df[["adresse", "code_postal", "ville"]] = df.apply(
                    utils.get_address, axis=1
                )
            elif old_col == "public_accueilli":
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
            elif old_col == "uniquement_sur_rdv":
                df[new_col] = df[old_col].astype(bool)
            elif old_col == "reprise":
                df[new_col] = _force_column_value(
                    df[old_col],
                    {
                        "1 pour 0": "1 pour 0",
                        "1 pour 1": "1 pour 1",
                        "non": "1 pour 0",
                        "oui": "1 pour 1",
                    },
                )
            elif old_col == "exclusivite_de_reprisereparation":
                df[new_col] = df[old_col].apply(lambda x: True if x == "oui" else False)
            else:
                df[new_col] = df[old_col]

    if "latitude" in df.columns and "longitude" in df.columns:
        df["latitude"] = df["latitude"].apply(mapping_utils.parse_float)
        df["longitude"] = df["longitude"].apply(mapping_utils.parse_float)
        df["location"] = df.apply(
            lambda row: utils.transform_location(row["longitude"], row["latitude"]),
            axis=1,
        )

    df["identifiant_unique"] = df.apply(
        lambda x: mapping_utils.create_identifiant_unique(
            x, source_name="CMA_REPARACTEUR" if reparacteurs else None
        ),
        axis=1,
    )
    df["cree_le"] = datetime.now()
    df["modifie_le"] = df["cree_le"]
    if "siret" in df.columns:
        df["siret"] = df["siret"].apply(mapping_utils.process_siret)
    if "telephone" in df.columns:
        df["telephone"] = df["telephone"].apply(mapping_utils.process_phone_number)

    df = df.replace({np.nan: None})

    duplicates_mask = df.duplicated("identifiant_unique", keep=False)
    duplicate_ids = df.loc[duplicates_mask, "identifiant_unique"].unique()
    number_of_duplicates = len(duplicate_ids)

    unique_source_ids = df["source_id"].unique()

    df_actors = df_displayedacteurs[
        (df_displayedacteurs["source_id"].isin(unique_source_ids))
        & (df_displayedacteurs["statut"] == "ACTIF")
    ]
    # TODO : est-ce que les colonne cree_le et modifie_le sont nécessaires
    df_missing_actors = df_actors[
        ~df_actors["identifiant_unique"].isin(df["identifiant_unique"])
    ][["identifiant_unique", "cree_le", "modifie_le"]]

    df_missing_actors["statut"] = "SUPPRIME"
    df_missing_actors["event"] = "UPDATE_ACTOR"

    metadata = {
        "number_of_duplicates": number_of_duplicates,
        "duplicate_ids": list(duplicate_ids),
        "added_rows": len(df),
        "number_of_removed_actors": len(df_missing_actors),
    }

    df = df.drop_duplicates(subset="identifiant_unique", keep="first")
    df["event"] = "CREATE"
    return {
        "df": df,
        "metadata": metadata,
        "config": config,
        "removed_actors": df_missing_actors,
    }


def create_labels(**kwargs):
    data_dict = kwargs["ti"].xcom_pull(task_ids="load_data_from_postgresql")
    labels = data_dict["labels"]
    df_acteurtype = data_dict["acteurtype"]
    df_actors = kwargs["ti"].xcom_pull(task_ids="create_actors")["df"]

    # Get ESS constant values to use in in the loop
    ess_acteur_type_id = df_acteurtype.loc[
        df_acteurtype["code"].str.lower() == "ess", "id"
    ].iloc[0]
    ess_label_id = labels.loc[labels["code"].str.lower() == "ess", "id"].iloc[0]
    ess_label_libelle = labels.loc[labels["code"].str.lower() == "ess", "libelle"].iloc[
        0
    ]

    label_mapping = labels.set_index(labels["code"].str.lower()).to_dict(orient="index")
    rows_list = []
    for _, row in df_actors.iterrows():

        # Handle label_code if it is set (works for reparacteur)
        label_code = row.get("label_code", "").lower()
        if label_code in label_mapping:
            rows_list.append(
                {
                    "acteur_id": row["identifiant_unique"],
                    "labelqualite_id": label_mapping[label_code]["id"],
                    "labelqualite": label_mapping[label_code]["libelle"],
                }
            )

        # Manage bonus reparation
        label = str(row.get("labels_etou_bonus"))
        if label == "Agréé Bonus Réparation":
            label_code = row.get("ecoorganisme").lower()
            if label_code in label_mapping.keys():
                rows_list.append(
                    {
                        "acteur_id": row["identifiant_unique"],
                        "labelqualite_id": label_mapping[label_code]["id"],
                        "labelqualite": label_mapping[label_code]["libelle"],
                    }
                )

        # Handle special case for ESS
        if row["acteur_type_id"] == ess_acteur_type_id:
            rows_list.append(
                {
                    "acteur_id": row["identifiant_unique"],
                    "labelqualite_id": ess_label_id,
                    "labelqualite": ess_label_libelle,
                }
            )

    df_labels = pd.DataFrame(
        rows_list, columns=["acteur_id", "labelqualite_id", "labelqualite"]
    )
    df_labels.drop_duplicates(
        ["acteur_id", "labelqualite_id"], keep="first", inplace=True
    )
    return df_labels


def create_acteur_services(**kwargs):
    data_dict = kwargs["ti"].xcom_pull(task_ids="load_data_from_postgresql")
    df_acteur_services = data_dict["acteur_services"]
    df_actors = kwargs["ti"].xcom_pull(task_ids="create_actors")["df"]

    acteurservice_acteurserviceid = {
        "Service de réparation": mapping_utils.get_id_from_code(
            "Service de réparation", df_acteur_services
        ),
        "Collecte par une structure spécialisée": mapping_utils.get_id_from_code(
            "Collecte par une structure spécialisée", df_acteur_services
        ),
    }
    acteurservice_eovalues = {
        "Service de réparation": [
            "point_dapport_de_service_reparation",
            "point_de_reparation",
        ],
        "Collecte par une structure spécialisée": [
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
                        "acteurservice": acteur_service,
                    }
                )

    df_acteur_services = pd.DataFrame(
        acteur_acteurservice_list,
        columns=["acteur_id", "acteurservice_id", "acteurservice"],
    )
    return df_acteur_services
