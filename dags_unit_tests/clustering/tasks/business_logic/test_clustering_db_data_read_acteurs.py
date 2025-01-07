from dags.clustering.tasks.business_logic.clustering_db_data_read_acteurs import (
    clustering_params_to_sql_query,
)


def test_clustering_params_to_sql_query():
    query = clustering_params_to_sql_query(
        table_name="qfdmo_displayedacteur",
        # SINOE, REFASHION
        include_source_ids=[6, 45],
        # Déchetteries
        include_acteur_type_ids=[7],
        include_if_all_fields_filled=["nom"],
        exclude_if_any_field_filled=["code_postal"],
    )
    print(query)
    # TODO: compléter les tests
