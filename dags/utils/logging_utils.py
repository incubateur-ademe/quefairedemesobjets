import json
import logging
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd

# TODO: improve by moving instantiation inside the functions
# and using inspect to get the parent caller's name
log = logging.getLogger(__name__)


class CustomJSONEncoder(json.JSONEncoder):
    """Fonction d'encodage JSON pour géré les types créés par
    la lecture DB ou pandas"""

    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        elif isinstance(obj, (np.integer, int)):
            return int(obj)
        elif isinstance(obj, (np.floating, float)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):  # Handle np.nan, pd.NA, None
            return None
        return super().default(obj)


def json_dumps(data: Any) -> str:
    """Fonction pour convertir un objet en JSON"""
    return json.dumps(data, cls=CustomJSONEncoder, indent=2, ensure_ascii=False)


def size_info_get(value: Any) -> Any:
    """Fonction pour obtenir la taille d'une valeur (par exemple
    pour afficher dans l'entête de la preview)"""
    if value is None:
        return 0
    elif isinstance(value, pd.DataFrame):
        return value.shape  # Rows * Columns
    elif isinstance(value, (list, set, tuple, np.ndarray)):
        return len(value)  # Number of entries
    elif isinstance(value, dict):
        return len(value.keys())  # Number of keys
    elif isinstance(value, (str, bytes)):
        return len(value)  # Length of string or bytes
    else:
        try:
            # Attempt to get the length for any other object with a length
            return len(value)
        except TypeError:
            return "unknown"


def preview(value_name: str, value: Any) -> None:
    """Aide à visualiser les données dans les logs de la console
    de manière cohérente et utile (ex: par défaut airflow xcom
    est tronqué lorsqu'il s'agit d'une dataframe).
    """
    size = size_info_get(value)
    log.info(f"::group::🔎 {value_name}: taille={size}, type={type(value).__name__}")
    if isinstance(value, pd.DataFrame):
        log.info("Détails des colonnes:")
        log.info(
            "\n"
            + value.dtypes.to_frame(name="Type")
            .reset_index()
            .rename(columns={"index": "Column"})
            .sort_values(by="Column", ascending=True)
            .to_string(index=False)
        )
        log.info("Première ligne:")
        log.info(json_dumps(value.head(1).to_dict(orient="records")))
        log.info("Dernière ligne:")
        log.info(json_dumps(value.tail(1).to_dict(orient="records")))
    elif isinstance(value, list):
        log.info(json_dumps(value))
    elif isinstance(value, dict):
        log.info(json_dumps(value))
    elif isinstance(value, set):
        log.info(json_dumps(list(value)))
    else:
        log.info(str(value))
    log.info("::endgroup::")
