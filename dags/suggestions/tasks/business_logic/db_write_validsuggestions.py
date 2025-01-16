import logging

from shared.tasks.database_logic.db_manager import PostgresConnectionManager
from sources.config import shared_constants as constants
from utils import logging_utils as log


def db_write_validsuggestions(data_from_db: dict):
    # If data_set is empty, nothing to do
    dag_run_id = data_from_db["dag_run_id"]
    engine = PostgresConnectionManager().engine
    if "actors" not in data_from_db:
        with engine.begin() as connection:
            update_suggestion_status(
                connection, dag_run_id, constants.SUGGESTION_ENCOURS
            )
        return
    df_actors = data_from_db["actors"]
    df_labels = data_from_db.get("labels")
    df_acteur_services = data_from_db.get("acteur_services")
    df_pds = data_from_db.get("pds")
    df_pdssc = data_from_db.get("pds_sous_categories")
    dag_run_id = data_from_db["dag_run_id"]
    change_type = data_from_db.get("change_type", "CREATE")

    with engine.begin() as connection:
        if change_type in [
            constants.SUGGESTION_SOURCE_AJOUT,
            constants.SUGGESTION_SOURCE_MISESAJOUR,
        ]:
            db_write_acteurupdate(
                connection, df_actors, df_labels, df_acteur_services, df_pds, df_pdssc
            )
        elif change_type == constants.SUGGESTION_SOURCE_SUPRESSION:
            db_write_acteurdelete(connection, df_actors)
        else:
            raise ValueError("Invalid change_type")

        update_suggestion_status(connection, dag_run_id, constants.SUGGESTION_SUCCES)


def db_write_acteurupdate(
    connection, df_actors, df_labels, df_acteur_services, df_pds, df_pdssc
):
    logging.warning("Création ou mise à jour des acteurs")

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


def db_write_acteurdelete(connection, df_acteur_to_delete):
    # mettre le statut des acteur à "SUPPRIMER" pour tous les acteurs à supprimer
    logging.warning("Suppression des acteurs")
    identifiant_uniques = list(
        set(df_acteur_to_delete[["identifiant_unique"]].values.flatten())
    )
    quoted_identifiant_uniques = [
        f"'{identifiant_unique}'" for identifiant_unique in identifiant_uniques
    ]
    query_acteur_to_delete = f"""
        UPDATE qfdmo_acteur
        SET statut='{constants.ACTEUR_SUPPRIME}'
        WHERE identifiant_unique IN ({",".join(quoted_identifiant_uniques)});
        UPDATE qfdmo_revisionacteur
        SET statut='{constants.ACTEUR_SUPPRIME}'
        WHERE identifiant_unique IN ({",".join(quoted_identifiant_uniques)});
        """
    log.preview("query_acteur_to_delete", query_acteur_to_delete)
    connection.execute(query_acteur_to_delete)


def update_suggestion_status(
    connection, suggestion_id, statut=constants.SUGGESTION_ENCOURS
):
    query = f"""
    UPDATE data_suggestioncohorte
    SET statut = '{statut}'
    WHERE id = {suggestion_id};
    """
    connection.execute(query)
