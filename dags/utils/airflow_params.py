"""Utilitaires pour travailler avec les Params UI Airflow.
https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/params.html
"""

import re

ID_PREFIX = "id="


def airflow_params_dropdown_from_mapping(mapping: dict[str, int]) -> list[str]:
    """Transforme un mapping de codes à IDs en dropdowns pour Airflow
    avec le format "{code} (id={ID})". L'inclusion des IDs est utile
    pour:
        - chercher par ID
        - confirmer qu'on a bien sélectionné le bon code (parfois les codes
            se ressemblent et les IDs enlèvent l'ambiguïté)

    Args:
        mapping (dict[str, int]): Mapping entre les codes et les IDs

    Returns:
        list[str]: Dropdowns pour Airflow
    """
    ids = list(mapping.values())
    if len(ids) != len(set(ids)):
        raise ValueError("Mapping invalide avec des IDs en doublon")
    return list(f"{code} ({ID_PREFIX}{id})" for code, id in mapping.items())


def airflow_params_dropdown_selected_to_ids(
    mapping_ids_by_codes: dict[str, int],
    dropdown_selected: list[str],
) -> list[int]:
    """Récupère les IDs correspondants aux valeurs
    sélectionnées dans un dropdown Params UI Airflow
    "{code} (id={ID})" => extrait le {code} => trouve l'ID correspondant
    via le mapping.

    Ceci permet de vérifier que les valeurs sélectionnées sont valides
    sans prendre le risque de faire confiance naïvement à l'ordonnencement
    des valeurs dans le dropdown qu'on ne maitrise pas.

    Args:
        mapping_id_by_code (dict[str, int]): Mapping entre les codes et les IDs
        dropdown_all (list[str]): Toutes les valeurs possibles du dropdown
        dropdown_selected (list[str]): Valeurs sélectionnées dans le dropdown

    Returns:
        list[int]: IDs correspondant aux valeurs sélectionnées
    """
    invalid = [x for x in dropdown_selected if ID_PREFIX not in x]
    if invalid:
        raise ValueError(
            f"""Valeurs invalides sans ID_PREFIX {ID_PREFIX}: {invalid}.
                         Utiliser airflow_params_dropdown_from_mapping
                         pour générer les dropdowns."""
        )
    codes = [re.sub(r" \(id=\d+\)$", "", v) for v in dropdown_selected]
    return [mapping_ids_by_codes[x] for x in codes]
