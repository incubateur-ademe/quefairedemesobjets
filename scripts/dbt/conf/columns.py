"""Constants and utilities for columns"""

import re
from collections import OrderedDict
from re import Pattern

# Mapping of column patterns and definitions
COLUMNS: dict[Pattern[str], dict] = {
    re.compile(r"etat_administratif"): {
        "description": "Etat administratif (A = Actif, C = Cessé d'activité)",
        "data_type": "varchar(1)",
        "data_tests": [
            "not_null",
            {"name": "accepted_values", "config": {"values": ["A", "C"]}},
        ],
    },
    # Boolean columns
    re.compile(r"((^|_)is_|(^|_)has_)"): {
        "description": "Boolean",
        "data_type": "boolean",
        "data_tests": [
            "not_null",
            {"name": "accepted_values", "config": {"values": ["true", "false"]}},
        ],
    },
    # Id columns
    re.compile(r"(^id$|_id$|identifiant_unique)"): {
        "description": "Identifiant",
        "data_type": "string",
        "data_tests": ["not_null"],
    },
    re.compile(r"siret"): {
        "description": "Siret",
        "data_type": "varchar(14)",
        "data_tests": ["not_null"],
    },
    re.compile(r"siren"): {
        "description": "Siren",
        "data_type": "varchar(9)",
        "data_tests": ["not_null"],
    },
    re.compile(r"statut"): {
        "description": "Statut",
        "data_type": "string",
        "data_tests": [
            {
                "name": "accepted_values",
                "config": {"values": ["ACTIF", "INACTIF"]},
            }
        ],
    },
}


def db_column_to_dbt_column(model_name: str, column: dict) -> dict:
    """Convert a column to a dbt schema"""
    col = next((v for k, v in COLUMNS.items() if k.search(column["name"])), None)
    if col is None:
        return OrderedDict(
            {
                "name": column["name"],
                "description": column["name"],
                "data_type": "string",
            }
        )
    col = OrderedDict([("name", column["name"])] + list(col.items()))
    return col
