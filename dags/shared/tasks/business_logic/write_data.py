from utils.dag_eo_utils import insert_suggestion_and_process_df


def write_data(
    dag_name: str,
    run_id: str,
    dfs: dict,
    metadata_actors: dict,
    metadata_acteur_to_delete: dict,
    metadata_pds: dict,
):

    metadata = {**metadata_actors, **metadata_acteur_to_delete, **metadata_pds}

    for key, data in dfs.items():
        # TODO dag_id
        dag_name_suffixed = (
            dag_name if key == "all" else f"{dag_name} - {key.replace('_', ' ')}"
        )
        run_name = run_id.replace("__", " - ")
        df = data["df"]
        metadata.update(data.get("metadata", {}))
        insert_suggestion_and_process_df(df, metadata, dag_name_suffixed, run_name)
