import pandas as pd
from shared.tasks.database_logic.db_manager import PostgresConnectionManager


def db_data_write(
    df_acteur_merged=pd.DataFrame,
    df_labels_updated=pd.DataFrame,
    df_acteur_services_updated=pd.DataFrame,
    df_acteur_sources_updated=pd.DataFrame,
    df_propositionservice_merged=pd.DataFrame,
    df_propositionservice_sous_categories_merged=pd.DataFrame,
):

    df_propositionservice_sous_categories_merged.rename(
        columns={"propositionservice_id": "displayedpropositionservice_id"},
        inplace=True,
    )

    engine = PostgresConnectionManager().engine

    original_table_name_actor = "qfdmo_displayedacteur"
    temp_table_name_actor = "qfdmo_displayedacteurtemp"

    original_table_name_labels = "qfdmo_displayedacteur_labels"
    temp_table_name_labels = "qfdmo_displayedacteurtemp_labels"

    original_table_name_acteur_services = "qfdmo_displayedacteur_acteur_services"
    temp_table_name_acteur_services = "qfdmo_displayedacteurtemp_acteur_services"

    original_table_name_sources = "qfdmo_displayedacteur_sources"
    temp_table_name_sources = "qfdmo_displayedacteurtemp_sources"

    original_table_name_ps = "qfdmo_displayedpropositionservice"
    temp_table_name_ps = "qfdmo_displayedpropositionservicetemp"

    original_table_name_pssc = "qfdmo_displayedpropositionservice_sous_categories"
    temp_table_name_pssc = "qfdmo_displayedpropositionservicetemp_sous_categories"

    with engine.connect() as conn:
        conn.execute(f"DELETE FROM {temp_table_name_pssc}")
        conn.execute(f"DELETE FROM {temp_table_name_ps}")
        conn.execute(f"DELETE FROM {temp_table_name_labels}")
        conn.execute(f"DELETE FROM {temp_table_name_acteur_services}")
        conn.execute(f"DELETE FROM {temp_table_name_sources}")
        conn.execute(f"DELETE FROM {temp_table_name_actor}")

        df_acteur_merged[
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
                "nom_officiel",
                "siren",
                "siret",
                "identifiant_externe",
                "acteur_type_id",
                "statut",
                "source_id",
                "cree_le",
                "modifie_le",
                "naf_principal",
                "commentaires",
                "horaires_osm",
                "horaires_description",
                "description",
                "public_accueilli",
                "reprise",
                "exclusivite_de_reprisereparation",
                "uniquement_sur_rdv",
                "action_principale_id",
                "uuid",
            ]
        ].to_sql(
            temp_table_name_actor,
            engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

        df_labels_updated[["displayedacteur_id", "labelqualite_id"]].to_sql(
            temp_table_name_labels,
            engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

        df_acteur_sources_updated[["displayedacteur_id", "source_id"]].to_sql(
            temp_table_name_sources,
            engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

        df_acteur_services_updated[["displayedacteur_id", "acteurservice_id"]].to_sql(
            temp_table_name_acteur_services,
            engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

        df_propositionservice_merged[["id", "action_id", "acteur_id"]].to_sql(
            temp_table_name_ps,
            engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

        df_propositionservice_sous_categories_merged[
            ["displayedpropositionservice_id", "souscategorieobjet_id"]
        ].to_sql(
            temp_table_name_pssc,
            engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=1000,
        )

    with engine.begin() as conn:
        conn.execute(
            f"ALTER TABLE {original_table_name_actor} "
            f"RENAME TO {original_table_name_actor}_old"
        )
        conn.execute(
            f"ALTER TABLE {temp_table_name_actor} "
            f"RENAME TO {original_table_name_actor}"
        )
        conn.execute(
            f"ALTER TABLE {original_table_name_actor}_old "
            f"RENAME TO {temp_table_name_actor}"
        )

        conn.execute(
            f"ALTER TABLE {original_table_name_labels} "
            f"RENAME TO {original_table_name_labels}_old"
        )
        conn.execute(
            f"ALTER TABLE {temp_table_name_labels} "
            f"RENAME TO {original_table_name_labels}"
        )
        conn.execute(
            f"ALTER TABLE {original_table_name_labels}_old "
            f"RENAME TO {temp_table_name_labels}"
        )
        conn.execute(
            f"ALTER TABLE {original_table_name_sources} "
            f"RENAME TO {original_table_name_sources}_old"
        )
        conn.execute(
            f"ALTER TABLE {temp_table_name_sources} "
            f"RENAME TO {original_table_name_sources}"
        )
        conn.execute(
            f"ALTER TABLE {original_table_name_sources}_old "
            f"RENAME TO {temp_table_name_sources}"
        )

        conn.execute(
            f"ALTER TABLE {original_table_name_acteur_services} "
            f"RENAME TO {original_table_name_acteur_services}_old"
        )
        conn.execute(
            f"ALTER TABLE {temp_table_name_acteur_services} "
            f"RENAME TO {original_table_name_acteur_services}"
        )
        conn.execute(
            f"ALTER TABLE {original_table_name_acteur_services}_old "
            f"RENAME TO {temp_table_name_acteur_services}"
        )

        conn.execute(
            f"ALTER TABLE {original_table_name_ps} "
            f"RENAME TO {original_table_name_ps}_old"
        )
        conn.execute(
            f"ALTER TABLE {temp_table_name_ps} " f"RENAME TO {original_table_name_ps}"
        )
        conn.execute(
            f"ALTER TABLE {original_table_name_ps}_old "
            f"RENAME TO {temp_table_name_ps}"
        )

        conn.execute(
            f"ALTER TABLE {original_table_name_pssc} "
            f"RENAME TO {original_table_name_pssc}_old"
        )
        conn.execute(
            f"ALTER TABLE {temp_table_name_pssc} "
            f"RENAME TO {original_table_name_pssc}"
        )
        conn.execute(
            f"ALTER TABLE {original_table_name_pssc}_old "
            f"RENAME TO {temp_table_name_pssc}"
        )

    print("Table swap completed successfully.")
