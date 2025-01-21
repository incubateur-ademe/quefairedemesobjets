import json
from pathlib import Path

import requests
from sources.tasks.transform.transform_column import (
    cast_eo_boolean_or_string_to_boolean,
    clean_acteur_type_code,
    clean_code_postal,
    clean_public_accueilli,
    clean_reprise,
    clean_siren,
    clean_siret,
    clean_souscategorie_codes,
    clean_souscategorie_codes_sinoe,
    clean_url,
    convert_opening_hours,
    strip_lower_string,
    strip_string,
)
from sources.tasks.transform.transform_df import (
    clean_acteurservice_codes,
    clean_action_codes,
    clean_adresse,
    clean_identifiant_externe,
    clean_identifiant_unique,
    clean_label_codes,
    clean_siret_and_siren,
    clean_telephone,
    compute_location,
    get_latlng_from_geopoint,
    merge_and_clean_souscategorie_codes,
    merge_sous_categories_columns,
)

PATH_NOMENCLARURE_DECHET = (
    "https://data.ademe.fr/data-fair/api/v1/datasets/sinoe-r-nomenclature-dechets/lines"
    "?size=10000"
)
KEY_CODE_DECHET = "C_TYP_DECHET"
KEY_LIBELLE_DECHET = "L_TYP_DECHET"
KEY_LIBELLE_DECHET_ALT = "LST_TYP_DECHET"


TRANSFORMATION_MAPPING = {
    "convert_opening_hours": convert_opening_hours,
    "clean_siren": clean_siren,
    "clean_siret": clean_siret,
    "strip_string": strip_string,
    "clean_siret_and_siren": clean_siret_and_siren,
    "clean_acteur_type_code": clean_acteur_type_code,
    "clean_identifiant_externe": clean_identifiant_externe,
    "clean_identifiant_unique": clean_identifiant_unique,
    "clean_telephone": clean_telephone,
    "merge_sous_categories_columns": merge_sous_categories_columns,
    "clean_adresse": clean_adresse,
    "clean_public_accueilli": clean_public_accueilli,
    "cast_eo_boolean_or_string_to_boolean": cast_eo_boolean_or_string_to_boolean,
    "clean_reprise": clean_reprise,
    "clean_acteurservice_codes": clean_acteurservice_codes,
    "clean_label_codes": clean_label_codes,
    "clean_code_postal": clean_code_postal,
    "clean_action_codes": clean_action_codes,
    "clean_souscategorie_codes": clean_souscategorie_codes,
    "merge_and_clean_souscategorie_codes": merge_and_clean_souscategorie_codes,
    "clean_url": clean_url,
    "clean_souscategorie_codes_sinoe": clean_souscategorie_codes_sinoe,
    "get_latlng_from_geopoint": get_latlng_from_geopoint,
    "strip_lower_string": strip_lower_string,
    "compute_location": compute_location,
}


# TODO: dataclass à implémenter pour la validation des paramètres des DAGs
class AirflowParams:
    pass


def get_mapping_config(mapping_key: str = "sous_categories"):
    config_path = Path(__file__).parent / "db_mapping.json"
    with open(config_path, "r") as f:
        config = json.load(f)
    return config[mapping_key]


def source_sinoe_dechet_mapping_get():
    """Mapping de C_TYP_DECHET (ex: "01")
    vers L_TYP_DECHET (ex: "Déchets de composés chimiques")
    {
    "total": 232,
    "results": [
        {
        "_rand": 237210,
        "C_TYP_DECHET": "01",
        "_i": 1,
        "NIV_HIER": 1,
        "L_TYP_DECHET": "Déchets de composés chimiques",
        "_score": null,
        "_id": "4UbH7jVe1hc_lXPc0oWz9"
        },
    """
    data = requests.get(PATH_NOMENCLARURE_DECHET).json()
    # Attention on a eu des renommage L_TYP_DECHET <-> LST_TYP_DECHET par le passé
    # d'où le get sur les deux clés
    return {
        x[KEY_CODE_DECHET]: x.get(KEY_LIBELLE_DECHET, None)
        or x.get(KEY_LIBELLE_DECHET_ALT)
        for x in data["results"]
    }
