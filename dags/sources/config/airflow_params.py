import json
from pathlib import Path

import requests
from sources.tasks.transform.transform_column import convert_opening_hours

PATH_NOMENCLARURE_DECHET = (
    "https://data.ademe.fr/data-fair/api/v1/datasets/sinoe-r-nomenclature-dechets/lines"
    "?size=10000"
)
KEY_CODE_DECHET = "C_TYP_DECHET"
KEY_LIBELLE_DECHET = "L_TYP_DECHET"
KEY_LIBELLE_DECHET_ALT = "LST_TYP_DECHET"


TRANSFORMATION_MAPPING = {"convert_opening_hours": convert_opening_hours}


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
