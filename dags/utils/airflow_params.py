"""Utilities to work with Airflow UI params.
https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/params.html

🔴 Beware of performance impact, see min_file_process_interval
https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html#config-scheduler-min-file-process-interval
https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#top-level-python-code
"""

import re

from utils.django import django_setup_full

django_setup_full()

ID_PREFIX = "id="


# TODO: legacy clustering, delete and use last function instead (values_display)
def airflow_params_dropdown_from_mapping(mapping: dict[str, int]) -> list[str]:
    """Turns a {code:id} mapping into a list of "{code} (id={ID})
    strings to use in Airflow Params UI"""
    ids = list(mapping.values())
    if len(ids) != len(set(ids)):
        raise ValueError("Mapping invalide avec des IDs en doublon")
    return list(f"{code} ({ID_PREFIX}{id})" for code, id in mapping.items())


# TODO: legacy clustering, delete and use last function instead (values_display)
def airflow_params_dropdown_selected_to_ids(
    mapping_ids_by_codes: dict[str, int],
    dropdown_selected: list[str],
) -> list[int]:
    """Retrieves IDs from selected dropdown values generated
    via airflow_params_dropdown_from_mapping"""
    if not dropdown_selected:
        return []
    invalid = [x for x in dropdown_selected if ID_PREFIX not in x]
    if invalid:
        raise ValueError(
            f"""Valeurs invalides sans ID_PREFIX {ID_PREFIX}: {invalid}.
                         Utiliser airflow_params_dropdown_from_mapping
                         pour générer les dropdowns."""
        )
    codes = [re.sub(r" \(id=\d+\)$", "", v) for v in dropdown_selected]
    # Si des codes n'ont pas bien étés extraits où ne sont pas dans le mapping
    missing = [x for x in codes if x not in mapping_ids_by_codes]
    if missing:
        raise ValueError(f"Codes non trouvés dans le mapping: {missing}")
    return [mapping_ids_by_codes[x] for x in codes]


def airflow_params_dropdown_codes_to_ids(model_name: str) -> dict[str, str]:
    """Returns a mapping of {code (id=id)} -> id so it can be used in Airflow Params UI:
    - keys = used in Param.examples = what user sees/selects
    - whole dict = used in Param.values_display = converts selections back to ids"""
    from qfdmo.models import ActeurType, Source

    models = {
        "Source": Source,
        "ActeurType": ActeurType,
    }
    entries = models[model_name].objects.all()
    return {
        str(id): f"{code} ({ID_PREFIX}{id})"
        for id, code in entries.values_list("id", "code")
    }
