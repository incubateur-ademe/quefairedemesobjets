"""
Fonction pour valider la configuration de clustering
"""

from utils.airflow_params import airflow_params_dropdown_selected_to_ids


def clustering_acteur_config_validate(
    mapping_source_id_by_code: dict[str, int],
    mapping_acteur_type_id_by_code: dict[str, int],
    include_source_codes: list[str],
    include_acteur_type_codes: list[str],
    include_if_all_fields_filled: list[str],
    exclude_if_any_field_filled: list[str],
) -> tuple:
    """Fonction de validation de la config de clustering"""
    include_source_ids = airflow_params_dropdown_selected_to_ids(
        mapping_ids_by_codes=mapping_source_id_by_code,
        dropdown_selected=include_source_codes,
    )
    include_acteur_type_ids = airflow_params_dropdown_selected_to_ids(
        mapping_ids_by_codes=mapping_acteur_type_id_by_code,
        dropdown_selected=include_acteur_type_codes,
    )
    fields_incl_excl = set(include_if_all_fields_filled) & set(
        exclude_if_any_field_filled
    )

    if not include_source_ids:
        raise ValueError("Au moins une source doit être sélectionnée")

    if not include_acteur_type_ids:
        raise ValueError("Au moins un type d'acteur doit être sélectionné")

    if not include_if_all_fields_filled:
        raise ValueError("Au moins un champ non vide doit être sélectionné")

    if fields_incl_excl:
        raise ValueError(f"Champs à la fois à inclure et à exclure: {fields_incl_excl}")

    return include_source_ids, include_acteur_type_ids
