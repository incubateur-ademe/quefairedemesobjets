import logging
from datetime import datetime

import pandas as pd
from sources.config import shared_constants
from utils import base_utils, mapping_utils

logging.basicConfig(level=logging.INFO)


def process_many2many_df(df, column_name, df_columns=["acteur_id", "labelqualite_id"]):
    try:
        # Attempt to process the 'labels' column if it exists and is not empty
        normalized_df = df[column_name].dropna().apply(pd.json_normalize)
        if normalized_df.empty:
            return pd.DataFrame(
                columns=df_columns
            )  # Return empty DataFrame if no data to process
        else:
            return pd.concat(normalized_df.tolist(), ignore_index=True)
    except KeyError:
        # Handle the case where the specified column does not exist
        return pd.DataFrame(columns=df_columns)


def handle_create_event(df_actors, dag_run_id, engine):
    df_labels = process_many2many_df(df_actors, "labels")
    df_acteur_services = process_many2many_df(
        df_actors, "acteur_services", df_columns=["acteur_id", "acteurservice_id"]
    )

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
        "pds": df_pds[["id", "action_id", "acteur_id"]],
        "pds_sous_categories": df_pdssc[
            ["propositionservice_id", "souscategorieobjet_id"]
        ],
        "dag_run_id": dag_run_id,
        "labels": df_labels[["acteur_id", "labelqualite_id"]],
        "acteur_services": df_acteur_services[["acteur_id", "acteurservice_id"]],
        "change_type": "CREATE",
    }


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
    df_actors = df_actors[df_actors["status"] == shared_constants.SUGGESTION_ATRAITER]
    df_actors = df_actors.apply(mapping_utils.replace_with_selected_candidat, axis=1)
    df_actors[["adresse", "code_postal", "ville"]] = df_actors.apply(
        lambda row: base_utils.extract_details(row, col="adresse_candidat"), axis=1
    )

    df_actors["modifie_le"] = current_time
    df_actors["cree_le"] = df_actors["cree_le"].fillna(current_time)

    for column in update_required_columns:
        if column not in df_actors.columns:
            df_actors[column] = None

    return {
        "actors": df_actors[update_required_columns],
        "dag_run_id": dag_run_id,
        "change_type": "UPDATE_ACTOR",
    }


def handle_write_data_create_event(
    connection, df_actors, df_labels, df_acteur_services, df_pds, df_pdssc
):
    df_actors[["identifiant_unique"]].to_sql(
        "temp_actors", connection, if_exists="replace"
    )

    delete_queries = [
        """
        DELETE FROM qfdmo_propositionservice_sous_categories
        WHERE propositionservice_id IN (
            SELECT id FROM qfdmo_propositionservice
            WHERE acteur_id IN ( SELECT identifiant_unique FROM temp_actors )
        );
        """,
        """
        DELETE FROM qfdmo_acteur_labels
        WHERE acteur_id IN ( SELECT identifiant_unique FROM temp_actors );
        """,
        """
        DELETE FROM qfdmo_acteur_acteur_services
        WHERE acteur_id IN ( SELECT identifiant_unique FROM temp_actors );
        """,
        """
        DELETE FROM qfdmo_propositionservice
        WHERE acteur_id IN ( SELECT identifiant_unique FROM temp_actors );
        """,
        """
        DELETE FROM qfdmo_acteur WHERE identifiant_unique
        IN ( SELECT identifiant_unique FROM temp_actors);
        """,
    ]

    for query in delete_queries:
        connection.execute(query)

    # Liste des colonnes souhaitées
    collection = connection.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name ="
        " 'qfdmo_acteur';"
    )
    colonnes_souhaitees = [col[0] for col in collection]

    # Filtrer les colonnes qui existent dans le DataFrame
    colonnes_existantes = [
        col for col in colonnes_souhaitees if col in df_actors.columns
    ]

    df_actors[colonnes_existantes].to_sql(
        "qfdmo_acteur",
        connection,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    df_labels = df_labels[["acteur_id", "labelqualite_id"]]
    df_labels.drop_duplicates(inplace=True)
    df_labels[["acteur_id", "labelqualite_id"]].to_sql(
        "qfdmo_acteur_labels",
        connection,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    df_acteur_services = df_acteur_services[["acteur_id", "acteurservice_id"]]
    df_acteur_services.drop_duplicates(inplace=True)
    df_acteur_services.to_sql(
        "qfdmo_acteur_acteur_services",
        connection,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    df_pds[["id", "action_id", "acteur_id"]].to_sql(
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
                    lambda row: mapping_utils.combine_comments(
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


def update_dag_run_status(
    connection, dag_run_id, statut=shared_constants.SUGGESTION_SUCCES
):
    query = f"""
    UPDATE data_suggestioncohorte SET statut = '{statut}' WHERE id = {dag_run_id}
    """
    connection.execute(query)
