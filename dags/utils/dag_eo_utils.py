import json
import logging
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
from airflow.providers.postgres.hooks.postgres import PostgresHook

logger = logging.getLogger(__name__)

env = Path(__file__).parent.parent.name

utils = import_module(f"{env}.utils.utils")
api_utils = import_module(f"{env}.utils.api_utils")
mapping_utils = import_module(f"{env}.utils.mapping_utils")


def fetch_data_from_api(**kwargs):
    params = kwargs["params"]
    api_url = params["endpoint"]
    logger.info(f"Fetching data from API : {api_url}")
    data = api_utils.fetch_dataset_from_point_apport(api_url)
    df = pd.DataFrame(data)
    return df


def create_proposition_services(**kwargs):
    df = kwargs["ti"].xcom_pull(task_ids="create_actors")["df"]
    data_dict = kwargs["ti"].xcom_pull(task_ids="load_data_from_postgresql")
    idx_max = data_dict["max_pds_idx"]
    rows_dict = {}
    merged_count = 0
    df_actions = data_dict["actions"]
    df_acteur_services = data_dict["acteur_services"]

    for _, row in df.iterrows():
        acteur_id = row["identifiant_unique"]
        sous_categories = row["produitsdechets_acceptes"]

        conditions = [
            ("point_dapport_de_service_reparation", "Service de réparation", "reparer"),
            (
                "point_dapport_pour_reemploi",
                "Collecte par une structure spécialisée",
                "donner",
            ),
            ("point_de_reparation", "Service de réparation", "reparer"),
            (
                "point_de_collecte_ou_de_reprise_des_dechets",
                "Collecte par une structure spécialisée",
                "trier",
            ),
        ]

        for condition, acteur_service_name, action_name in conditions:
            if row.get(condition):
                acteur_service_id = mapping_utils.get_id_from_code(
                    acteur_service_name, df_acteur_services
                )
                action_id = mapping_utils.get_id_from_code(action_name, df_actions)
                key = (acteur_service_id, action_id, acteur_id)

                if key in rows_dict:
                    if sous_categories not in rows_dict[key]["sous_categories"]:
                        merged_count = +merged_count
                        rows_dict[key]["sous_categories"] += " | " + sous_categories
                else:
                    rows_dict[key] = {
                        "acteur_service_id": acteur_service_id,
                        "action_id": action_id,
                        "acteur_id": acteur_id,
                        "action": action_name,
                        "acteur_service": acteur_service_name,
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

    rows_list = []
    sous_categories = config["sous_categories"]

    for index, row in df.iterrows():
        products = str(row["sous_categories"]).split("|")
        for product in set(products):
            if product.strip().lower() in sous_categories:
                rows_list.append(
                    {
                        "propositionservice_id": row["id"],
                        "souscategorieobjet_id": mapping_utils.get_id_from_code(
                            sous_categories[product.strip().lower()],
                            df_sous_categories_map,
                        ),
                        "souscategorie": product.strip(),
                    }
                )

    df_sous_categories = pd.DataFrame(
        rows_list,
        columns=["propositionservice_id", "souscategorieobjet_id", "souscategorie"],
    )
    return df_sous_categories


def serialize_to_json(**kwargs):
    df_actors = kwargs["ti"].xcom_pull(task_ids="create_actors")["df"]
    df_pds = kwargs["ti"].xcom_pull(task_ids="create_proposition_services")["df"]
    df_pdsc = kwargs["ti"].xcom_pull(
        task_ids="create_proposition_services_sous_categories"
    )
    df_pdsc.drop_duplicates(
        ["propositionservice_id", "souscategorieobjet_id"], keep="first", inplace=True
    )
    df_pdsc = df_pdsc[df_pdsc["souscategorieobjet_id"].notna()]
    df_labels = kwargs["ti"].xcom_pull(task_ids="create_labels")

    aggregated_pdsc = (
        df_pdsc.groupby("propositionservice_id")
        .apply(lambda x: x.to_dict("records") if not x.empty else [])
        .reset_index(name="pds_sous_categories")
    )

    df_pds_joined = pd.merge(
        df_pds,
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
        aggregated_labels.reset_index(name="labels")
        if len(aggregated_labels) > 0
        else pd.DataFrame(columns=["acteur_id", "labels"])
    )

    df_joined_with_pds = pd.merge(
        df_actors,
        aggregated_pds,
        how="left",
        left_on="identifiant_unique",
        right_on="acteur_id",
    )

    df_joined = pd.merge(
        df_joined_with_pds,
        aggregated_labels,
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

    return {"all": {"df": df_joined}}


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

    return {
        "acteurtype": df_acteurtype,
        "sources": df_sources,
        "actions": df_actions,
        "acteur_services": df_acteur_services,
        "max_pds_idx": max_id_pds,
        "sous_categories": df_sous_categories_objet,
        "labels": df_label,
    }


def insert_dagrun_and_process_df(df, event, metadata, dag_id, run_id):
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

        df["change_type"] = event
        df["dag_run_id"] = dag_run_id
        df[["row_updates", "dag_run_id", "change_type"]].to_sql(
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
    event = kwargs.get("event", "CREATE")
    dfs = kwargs["ti"].xcom_pull(task_ids="serialize_actors_to_records")
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
        insert_dagrun_and_process_df(df, event, metadata, dag_id_suffixed, run_id)


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


def create_actors(**kwargs):
    data_dict = kwargs["ti"].xcom_pull(task_ids="load_data_from_postgresql")
    df = kwargs["ti"].xcom_pull(task_ids="fetch_data_from_api")
    df_sources = data_dict["sources"]
    df_acteurtype = data_dict["acteurtype"]
    config_path = Path(__file__).parent.parent / "config" / "db_mapping.json"

    with open(config_path, "r") as f:
        config = json.load(f)

    params = kwargs["params"]
    column_mapping = params["column_mapping"]
    column_to_drop = params.get("column_to_drop", [])
    column_to_replace = params.get("default_column_value", {})
    for k, val in column_to_replace.items():
        df[k] = val

    df["nom_de_lorganisme_std"] = df["nom_de_lorganisme"].str.replace("-", "")
    df["id_point_apport_ou_reparation"] = df["id_point_apport_ou_reparation"].fillna(
        df["nom_de_lorganisme_std"]
    )
    df["id_point_apport_ou_reparation"] = (
        df["id_point_apport_ou_reparation"]
        .str.replace(" ", "_")
        .str.replace("_-", "_")
        .str.replace("__", "_")
    )
    df = df.drop(column_to_drop, axis=1)
    df = df.dropna(subset=["latitudewgs84", "longitudewgs84"])
    df = df.replace({np.nan: None})
    for old_col, new_col in column_mapping.items():
        if new_col:
            if old_col == "type_de_point_de_collecte":
                df[new_col] = df[old_col].apply(
                    lambda x: mapping_utils.transform_acteur_type_id(
                        x, df_acteurtype=df_acteurtype
                    )
                )
            elif old_col in ["latitudewgs84", "longitudewgs84"]:
                df[new_col] = df.apply(
                    lambda row: utils.transform_location(
                        row["longitudewgs84"], row["latitudewgs84"]
                    ),
                    axis=1,
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
            elif old_col == "uniquement_sur_rdv":
                df[new_col] = df[old_col].fillna(False)
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
                df[new_col] = _force_column_value(
                    df[old_col], {"oui": True, "non": False}, False
                )
            else:
                df[new_col] = df[old_col]
    df["identifiant_unique"] = df.apply(
        lambda x: mapping_utils.create_identifiant_unique(x),
        axis=1,
    )
    df["statut"] = "ACTIF"
    df["latitude"] = df["latitudewgs84"].astype(float).replace({np.nan: None})
    df["longitude"] = df["longitudewgs84"].astype(float).replace({np.nan: None})
    df = df.drop(["latitudewgs84", "longitudewgs84"], axis=1)
    df["modifie_le"] = df["cree_le"]
    if "siret" in df.columns:
        df["siret"] = df["siret"].replace({np.nan: None})
        df["siret"] = df["siret"].astype(str).apply(lambda x: x[:14])
    if "telephone" in df.columns:
        df["telephone"] = df["telephone"].dropna().apply(lambda x: x.replace(" ", ""))
        df["telephone"] = (
            df["telephone"]
            .dropna()
            .apply(lambda x: "0" + x[2:] if x.startswith("33") else x)
        )
    if "service_a_domicile" in df.columns:
        df.loc[
            df["service_a_domicile"] == "service à domicile uniquement", "statut"
        ] = "SUPPRIME"

    duplicates_mask = df.duplicated("identifiant_unique", keep=False)
    duplicate_ids = df.loc[duplicates_mask, "identifiant_unique"].unique()

    number_of_duplicates = len(duplicate_ids)

    metadata = {
        "number_of_duplicates": number_of_duplicates,
        "duplicate_ids": list(duplicate_ids),
        "added_rows": len(df),
    }

    return {"df": df, "metadata": metadata, "config": config}


def create_labels(**kwargs):
    data_dict = kwargs["ti"].xcom_pull(task_ids="load_data_from_postgresql")
    labels = data_dict["labels"]
    df_acteurtype = data_dict["acteurtype"]
    df_actors = kwargs["ti"].xcom_pull(task_ids="create_actors")["df"]

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
        if "labels_etou_bonus" in row:
            label = str(row["labels_etou_bonus"])
            if label == "Agréé Bonus Réparation":
                eco_code = row["ecoorganisme"].lower()
                if eco_code in label_mapping:
                    rows_list.append(
                        {
                            "acteur_id": row["identifiant_unique"],
                            "labelqualite_id": label_mapping[eco_code]["id"],
                            "labelqualite": label_mapping[eco_code]["libelle"],
                        }
                    )

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
