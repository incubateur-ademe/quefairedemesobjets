import json
from pathlib import Path

import requests
from sources.config import shared_constants as constants
from sources.tasks.transform.transform_column import (
    cast_eo_boolean_or_string_to_boolean,
    clean_acteur_type_code,
    clean_code_list,
    clean_code_postal,
    clean_email,
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
    clean_service_a_domicile,
    clean_siret_and_siren,
    clean_telephone,
    clean_url_from_multi_columns,
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
    "clean_email": clean_email,
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
    "clean_service_a_domicile": clean_service_a_domicile,
    "clean_siret_and_siren": clean_siret_and_siren,
    "clean_telephone": clean_telephone,
    "clean_url_from_multi_columns": clean_url_from_multi_columns,
    "compute_location": compute_location,
    "get_latlng_from_geopoint": get_latlng_from_geopoint,
    "merge_sous_categories_columns": merge_sous_categories_columns,
}

TRANSFORMATION_MAPPING = {
    **TRANSFORM_COLUMN_MAPPING,
    **TRANSFORM_DF_MAPPING,
}


EO_NORMALIZATION_RULES = [
    # 1. Renommage des colonnes
    {
        "origin": "nom_de_lorganisme",
        "destination": "nom",
    },
    {
        "origin": "enseigne_commerciale",
        "destination": "nom_commercial",
    },
    {
        "origin": "longitudewgs84",
        "destination": "longitude",
    },
    {
        "origin": "latitudewgs84",
        "destination": "latitude",
    },
    # 2. Transformation des colonnes
    {
        "origin": "ecoorganisme",
        "transformation": "strip_lower_string",
        "destination": "source_code",
    },
    {
        "origin": "type_de_point_de_collecte",
        "transformation": "clean_acteur_type_code",
        "destination": "acteur_type_code",
    },
    {
        "origin": "public_accueilli",
        "transformation": "clean_public_accueilli",
        "destination": "public_accueilli",
    },
    {
        "origin": "exclusivite_de_reprisereparation",
        "transformation": "cast_eo_boolean_or_string_to_boolean",
        "destination": "exclusivite_de_reprisereparation",
    },
    {
        "origin": "reprise",
        "transformation": "clean_reprise",
        "destination": "reprise",
    },
    {
        "origin": "produitsdechets_acceptes",
        "transformation": "clean_sous_categorie_codes",
        "destination": "sous_categorie_codes",
    },
    {
        "origin": "consignes_dacces",
        "transformation": "strip_string",
        "destination": "consignes_dacces",
    },
    {
        "origin": "uniquement_sur_rdv",
        "transformation": "cast_eo_boolean_or_string_to_boolean",
        "destination": "uniquement_sur_rdv",
    },
    {
        "origin": "adresse_complement",
        "transformation": "strip_string",
        "destination": "adresse_complement",
    },
    {
        "origin": "consignes_dacces",
        "transformation": "strip_string",
        "destination": "consignes_dacces",
    },
    {
        "origin": "horaires_douverture",
        "transformation": "clean_horaires_osm",
        "destination": "horaires_osm",
    },
    {
        "origin": "site_web",
        "transformation": "clean_url",
        "destination": "url",
    },
    {
        "origin": "email",
        "transformation": "clean_email",
        "destination": "email",
    },
    # 3. Ajout des colonnes avec une valeur par défaut
    {
        "column": "statut",
        "value": constants.ACTEUR_ACTIF,
    },
    # 4. Transformation du dataframe
    {
        "origin": ["latitude", "longitude"],
        "transformation": "compute_location",
        "destination": ["location", "latitude", "longitude"],
    },
    {
        "origin": ["labels_etou_bonus", "acteur_type_code"],
        "transformation": "clean_label_codes",
        "destination": ["label_codes"],
    },
    {
        "origin": ["id_point_apport_ou_reparation", "nom", "acteur_type_code"],
        "transformation": "clean_identifiant_externe",
        "destination": ["identifiant_externe"],
    },
    {
        "origin": [
            "identifiant_externe",
            "source_code",
        ],
        "transformation": "clean_identifiant_unique",
        "destination": ["identifiant_unique"],
    },
    {
        "origin": ["siret", "siren"],
        "transformation": "clean_siret_and_siren",
        "destination": ["siret", "siren"],
    },
    {
        "origin": ["adresse_format_ban"],
        "transformation": "clean_adresse",
        "destination": ["adresse", "code_postal", "ville"],
    },
    {
        "origin": ["telephone", "code_postal"],
        "transformation": "clean_telephone",
        "destination": ["telephone"],
    },
    {
        "origin": [
            "point_dapport_de_service_reparation",
            "point_de_reparation",
            "point_dapport_pour_reemploi",
            "point_de_collecte_ou_de_reprise_des_dechets",
        ],
        "transformation": "clean_acteur_service_codes",
        "destination": ["acteur_service_codes"],
    },
    {
        "origin": [
            "point_dapport_de_service_reparation",
            "point_de_reparation",
            "point_dapport_pour_reemploi",
            "point_de_collecte_ou_de_reprise_des_dechets",
        ],
        "transformation": "clean_action_codes",
        "destination": ["action_codes"],
    },
    {
        "origin": ["action_codes", "sous_categorie_codes"],
        "transformation": "clean_proposition_services",
        "destination": ["proposition_service_codes"],
    },
    {
        "origin": ["service_a_domicile", "perimetre_dintervention"],
        "transformation": "clean_service_a_domicile",
        "destination": ["lieu_prestation", "perimetre_adomicile_codes"],
    },
    # {
    #     "origin": ["latitudemercator", "longitudemercator"],
    #     "transformation": "check_empty_columns",
    #     "destination": ["latitudemercator", "longitudemercator"],
    # },
    # 5. Supression des colonnes
    {"remove": "_i"},
    {"remove": "_id"},
    {"remove": "_updatedAt"},
    {"remove": "_rand"},
    {"remove": "_geopoint"},
    {"remove": "filiere"},
    {"remove": "_score"},
    {"remove": "adresse_format_ban"},
    {"remove": "id_point_apport_ou_reparation"},
    {"remove": "point_de_collecte_ou_de_reprise_des_dechets"},
    {"remove": "point_dapport_de_service_reparation"},
    {"remove": "point_dapport_pour_reemploi"},
    {"remove": "point_de_reparation"},
    {"remove": "perimetre_dintervention"},  # Not managed yet
    {"remove": "labels_etou_bonus"},
    {"remove": "latitudemercator"},  # check empty
    {"remove": "longitudemercator"},  # check empty
    {"remove": "accessible"},  # Not managed yet
    {"remove": "service_a_domicile"},  # Not managed yet
    {"remove": "date_fin_point_ephemere"},  # Not managed yet
    {"remove": "date_debut_point_ephemere"},  # Not managed yet
]


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
