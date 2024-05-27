import pandas as pd
from importlib import import_module
from pathlib import Path
from datetime import datetime
import json

env = Path(__file__).parent.parent.name

utils = import_module(f"{env}.utils.utils")


def process_labels(df, column_name):
    try:
        # Attempt to process the 'labels' column if it exists and is not empty
        normalized_labels = df[column_name].dropna().apply(pd.json_normalize)
        if normalized_labels.empty:
            return pd.DataFrame(
                columns=["acteur_id", "labelqualite_id"]
            )  # Return empty DataFrame if no data to process
        else:
            return pd.concat(normalized_labels.tolist(), ignore_index=True)
    except KeyError:
        # Handle the case where the specified column does not exist
        return pd.DataFrame(columns=["acteur_id", "labelqualite_id"])


def handle_create_event(df_actors, dag_run_id, engine):
    create_required_columns = [
        "identifiant_unique",
        "nom",
        "adresse",
        "adresse_complement",
        "code_postal",
        "ville",
        "url",
        "email",
        "location",
        "telephone",
        "nom_commercial",
        "siret",
        "identifiant_externe",
        "acteur_type_id",
        "statut",
        "source_id",
        "cree_le",
        "horaires_description",
        "modifie_le",
        "commentaires",
    ]

    for column in create_required_columns:
        if column not in df_actors.columns:
            df_actors[column] = None

    df_labels = process_labels(df_actors, "labels")

    max_id_pds = pd.read_sql_query(
        "SELECT max(id) FROM qfdmo_propositionservice", engine
    )["max"][0]
    normalized_pds_dfs = df_actors["proposition_services"].apply(pd.json_normalize)
    df_pds = pd.concat(normalized_pds_dfs.tolist(), ignore_index=True)
    ids_range = range(max_id_pds + 1, max_id_pds + 1 + len(df_pds))

    df_pds["id"] = ids_range
    df_pds["pds_sous_categories"] = df_pds.apply(
        lambda row: [
            {**d, "propositionservice_id": row["id"]}
            for d in row["pds_sous_categories"]
        ],
        axis=1,
    )

    normalized_pdssc_dfs = df_pds["pds_sous_categories"].apply(pd.json_normalize)
    df_pdssc = pd.concat(normalized_pdssc_dfs.tolist(), ignore_index=True)

    return {
        "actors": df_actors,
        "pds": df_pds[["id", "acteur_service_id", "action_id", "acteur_id"]],
        "pds_sous_categories": df_pdssc[
            ["propositionservice_id", "souscategorieobjet_id"]
        ],
        "dag_run_id": dag_run_id,
        "labels": df_labels[["acteur_id", "labelqualite_id"]],
        "change_type": "CREATE",
    }


def flatten_ae_results(row):
    if "ae_result" in row and pd.notna(row["ae_result"]):
        ae_result = row["ae_result"]
        for key, value in ae_result.items():
            row[f"{key}"] = value
        row = row.drop(labels=["ae_result"])
    return row


def handle_update_actor_event(df_actors, dag_run_id):
    update_required_columns = [
        "identifiant_unique",
        "adresse",
        "location",
        "commentaires",
        "statut",
        "code_postal",
        "ville",
        "modifie_le",
        "cree_le",
        "siret",
    ]

    current_time = datetime.now().astimezone().isoformat(timespec="microseconds")

    df_actors = df_actors.apply(flatten_ae_results, axis=1)
    df_actors["statut"] = df_actors.apply(
        lambda row: (
            "SUPPRIME"
            if row["ae_result.etat_admin"] == "F"
            and (row["ae_result.etat_admin_siege"] in ["F", None])
            else "ACTIF"
        ),
        axis=1,
    )
    df_actors["siret"] = df_actors.apply(
        lambda row: (
            row["ae_result.siret_siege"]
            if row["ae_result.etat_admin_siege"] == "A"
            else None
        ),
        axis=1,
    )
    df_actors[["adresse", "code_postal", "ville"]] = df_actors.apply(
        lambda row: utils.extract_details(row, col="ae_result.adresse"), axis=1
    )

    df_actors["modifie_le"] = current_time
    df_actors["cree_le"] = current_time

    for column in update_required_columns:
        if column not in df_actors.columns:
            df_actors[column] = None

    return {
        "actors": df_actors[update_required_columns],
        "dag_run_id": dag_run_id,
        "change_type": "UPDATE_ACTOR",
    }


def handle_write_data_create_event(connection, df_actors, df_labels, df_pds, df_pdssc):
    df_actors[
        [
            "identifiant_unique",
            "nom",
            "adresse",
            "adresse_complement",
            "code_postal",
            "ville",
            "url",
            "email",
            "location",
            "telephone",
            "nom_commercial",
            "siret",
            "identifiant_externe",
            "acteur_type_id",
            "statut",
            "source_id",
            "cree_le",
            "horaires_description",
            "modifie_le",
            "commentaires",
        ]
    ].to_sql("temp_actors", connection, if_exists="replace")

    delete_queries = [
        """
        DELETE FROM qfdmo_propositionservice_sous_categories
        WHERE propositionservice_id IN (
            SELECT id FROM qfdmo_propositionservice
            WHERE acteur_id IN (
                SELECT identifiant_unique FROM temp_actors
            )
        );
        """,
        """
             DELETE FROM qfdmo_acteur_labels
              WHERE acteur_id IN (
                     SELECT identifiant_unique FROM temp_actors
                  );
        """,
        """
        DELETE FROM qfdmo_propositionservice
        WHERE acteur_id IN (
            SELECT identifiant_unique FROM temp_actors
        );
        """,
        """
        DELETE FROM qfdmo_acteur WHERE identifiant_unique
        in ( select identifiant_unique from temp_actors);
        """,
    ]

    for query in delete_queries:
        connection.execute(query)

    df_actors[
        [
            "identifiant_unique",
            "nom",
            "adresse",
            "adresse_complement",
            "code_postal",
            "ville",
            "url",
            "email",
            "location",
            "telephone",
            "nom_commercial",
            "siret",
            "identifiant_externe",
            "acteur_type_id",
            "statut",
            "source_id",
            "cree_le",
            "horaires_description",
            "modifie_le",
            "commentaires",
        ]
    ].to_sql(
        "qfdmo_acteur",
        connection,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    df_labels[["acteur_id", "labelqualite_id"]].to_sql(
        "qfdmo_acteur_labels",
        connection,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    df_pds[["id", "acteur_service_id", "action_id", "acteur_id"]].to_sql(
        "qfdmo_propositionservice",
        connection,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    df_pdssc[["propositionservice_id", "souscategorieobjet_id"]].to_sql(
        "qfdmo_propositionservice_sous_categories",
        connection,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )


def combine_comments(existing_commentaires, new_commentaires):
    def parse_json_or_default(json_str, default):
        try:
            parsed_json = json.loads(json_str)
            return parsed_json if isinstance(parsed_json, list) else [default]
        except (json.JSONDecodeError, TypeError):
            return [default]

    existing_commentaires_json = (
        parse_json_or_default(existing_commentaires, {"message": existing_commentaires})
        if existing_commentaires
        else []
    )

    if new_commentaires:
        try:
            new_commentaires_json = json.loads(new_commentaires)
            if not isinstance(new_commentaires_json, dict):
                raise ValueError("New commentaires should be a JSON object")
            new_commentaires_json = [new_commentaires_json]
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError("New commentaires should be a valid JSON object") from e
    else:
        new_commentaires_json = []

    combined_commentaires = existing_commentaires_json + new_commentaires_json
    return json.dumps(combined_commentaires)


def handle_write_data_update_actor_event(connection, df_actors):
    df_actors.to_sql(
        "temp_actors",
        connection,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1000,
    )

    temp_tables_creation_query = """
        CREATE TEMP TABLE temp_existing_actors AS
        SELECT * FROM qfdmo_revisionacteur WHERE identifiant_unique IN (
            SELECT identifiant_unique FROM temp_actors
        );

        CREATE TEMP TABLE temp_existing_pds AS
        SELECT * FROM qfdmo_revisionpropositionservice WHERE acteur_id IN (
            SELECT identifiant_unique FROM temp_actors
        );

        CREATE TEMP TABLE temp_existing_pdssc AS
        SELECT * FROM qfdmo_revisionpropositionservice_sous_categories
        WHERE revisionpropositionservice_id IN (
            SELECT id FROM temp_existing_pds
        );
    """
    connection.execute(temp_tables_creation_query)

    delete_queries = """
        DELETE FROM qfdmo_revisionpropositionservice_sous_categories
        WHERE revisionpropositionservice_id IN (
            SELECT id FROM temp_existing_pds
        );

        DELETE FROM qfdmo_revisionpropositionservice
        WHERE acteur_id IN (
            SELECT identifiant_unique FROM temp_actors
        );

        DELETE FROM qfdmo_revisionacteur
        WHERE identifiant_unique IN (
            SELECT identifiant_unique FROM temp_actors
        );
    """
    connection.execute(delete_queries)

    temp_actors_df = pd.read_sql_query("SELECT * FROM temp_actors", connection)
    temp_existing_actors_df = pd.read_sql_query(
        "SELECT * FROM temp_existing_actors", connection
    )

    for column in temp_existing_actors_df.columns:
        if column not in temp_actors_df.columns:
            temp_actors_df[column] = None

    for column in temp_actors_df.columns:
        if column not in temp_existing_actors_df.columns:
            temp_existing_actors_df[column] = None

    combined_actors_df = pd.merge(
        temp_existing_actors_df,
        temp_actors_df,
        on="identifiant_unique",
        how="outer",
        suffixes=("_existing", "_new"),
    )

    for column in temp_existing_actors_df.columns:
        if column != "identifiant_unique":
            if column == "commentaires":
                combined_actors_df[column] = combined_actors_df.apply(
                    lambda row: combine_comments(
                        row[f"{column}_existing"], row[f"{column}_new"]
                    ),
                    axis=1,
                )
            else:
                combined_actors_df[column] = combined_actors_df[
                    f"{column}_new"
                ].combine_first(combined_actors_df[f"{column}_existing"])

    combined_actors_df = combined_actors_df[temp_existing_actors_df.columns]

    combined_actors_df.to_sql(
        "qfdmo_revisionacteur",
        connection,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    existing_pds_df = pd.read_sql_query("SELECT * FROM temp_existing_pds", connection)
    existing_pdssc_df = pd.read_sql_query(
        "SELECT * FROM temp_existing_pdssc", connection
    )

    existing_pds_df.to_sql(
        "qfdmo_revisionpropositionservice",
        connection,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    existing_pdssc_df.to_sql(
        "qfdmo_revisionpropositionservice_sous_categories",
        connection,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )


def update_dag_run_status(connection, dag_run_id):
    update_query = f"""
        UPDATE qfdmo_dagrun
        SET status = 'FINISHED'
        WHERE id = {dag_run_id}
        """
    connection.execute(update_query)
