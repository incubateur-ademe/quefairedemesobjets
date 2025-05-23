import json
from pathlib import Path

import requests
from sources.tasks.transform.transform_column import (
    cast_eo_boolean_or_string_to_boolean,
    clean_acteur_type_code,
    clean_code_list,
    clean_code_postal,
    clean_horaires_osm,
    clean_public_accueilli,
    clean_reprise,
    clean_siren,
    clean_siret,
    clean_sous_categorie_codes,
    clean_sous_categorie_codes_sinoe,
    clean_url,
    convert_opening_hours,
    strip_lower_string,
    strip_string,
)
from sources.tasks.transform.transform_df import (
    clean_acteur_service_codes,
    clean_action_codes,
    clean_adresse,
    clean_identifiant_externe,
    clean_identifiant_unique,
    clean_label_codes,
    clean_proposition_services,
    clean_siret_and_siren,
    clean_telephone,
    compute_location,
    get_latlng_from_geopoint,
    merge_sous_categories_columns,
)

from utils.django import django_setup_full

PATH_NOMENCLARURE_DECHET = (
    "https://data.ademe.fr/data-fair/api/v1/datasets/sinoe-r-nomenclature-dechets/lines"
    "?size=10000"
)
KEY_CODE_DECHET = "C_TYP_DECHET"
KEY_LIBELLE_DECHET = "L_TYP_DECHET"
KEY_LIBELLE_DECHET_ALT = "LST_TYP_DECHET"

TRANSFORM_COLUMN_MAPPING = {
    "cast_eo_boolean_or_string_to_boolean": cast_eo_boolean_or_string_to_boolean,
    "clean_acteur_type_code": clean_acteur_type_code,
    "clean_code_list": clean_code_list,
    "clean_code_postal": clean_code_postal,
    "clean_horaires_osm": clean_horaires_osm,
    "clean_public_accueilli": clean_public_accueilli,
    "clean_reprise": clean_reprise,
    "clean_siren": clean_siren,
    "clean_siret": clean_siret,
    "clean_sous_categorie_codes_sinoe": clean_sous_categorie_codes_sinoe,
    "clean_sous_categorie_codes": clean_sous_categorie_codes,
    "clean_url": clean_url,
    "convert_opening_hours": convert_opening_hours,
    "strip_lower_string": strip_lower_string,
    "strip_string": strip_string,
}

TRANSFORM_DF_MAPPING = {
    "clean_acteur_service_codes": clean_acteur_service_codes,
    "clean_action_codes": clean_action_codes,
    "clean_adresse": clean_adresse,
    "clean_identifiant_externe": clean_identifiant_externe,
    "clean_identifiant_unique": clean_identifiant_unique,
    "clean_label_codes": clean_label_codes,
    "clean_proposition_services": clean_proposition_services,
    "clean_siret_and_siren": clean_siret_and_siren,
    "clean_telephone": clean_telephone,
    "compute_location": compute_location,
    "get_latlng_from_geopoint": get_latlng_from_geopoint,
    "merge_sous_categories_columns": merge_sous_categories_columns,
}

TRANSFORMATION_MAPPING = {
    **TRANSFORM_COLUMN_MAPPING,
    **TRANSFORM_DF_MAPPING,
}


# TODO: dataclass à implémenter pour la validation des paramètres des DAGs
class AirflowParams:
    pass


def get_mapping_config(mapping_key: str = "sous_categories"):
    config_path = Path(__file__).parent / "db_mapping.json"
    with open(config_path, "r") as f:
        config = json.load(f)
    return config[mapping_key]


def get_souscategorie_mapping_from_db():
    django_setup_full()
    from qfdmo.models.categorie_objet import SousCategorieObjet

    return {
        souscategorie.code: souscategorie.code
        for souscategorie in SousCategorieObjet.objects.all()
    }


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
