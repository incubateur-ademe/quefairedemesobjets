import inspect
import json
import logging
import math
import os
import re
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel


def logger_get(levels: int = 3) -> logging.Logger:
    """Utilitaire pour obtenir le logger avec nom du fichier appelant
    source, sinon tous les logs ont le nom du fichier courant
    (logging_utils) ce qui perd de l'intérêt pour le logging.

    Ajuster levels en fonction du nestage des fonctions, par défaut
    2 niveaux pour skipper logger_get + preview et obtenir la source"""
    caller_name = os.path.basename(inspect.stack()[levels].filename)
    return logging.getLogger(caller_name)


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
        return str(obj)


def json_dumps(data: Any) -> str:
    """Fonction pour convertir un objet en JSON"""
    return json.dumps(data, cls=CustomJSONEncoder, indent=4, ensure_ascii=False)


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
    elif isinstance(value, BaseModel):
        return f"{len(value.model_fields.keys())} propriétés"
    elif isinstance(value, (str, bytes)):
        return len(value)  # Length of string or bytes
    elif isinstance(value, (int, float, bool, np.integer, np.floating)):
        return value
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
    log = logger_get()
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
        log.info("3 premières entrées:")
        log.info(json_dumps(value[:3]))
    elif isinstance(value, dict):
        log.info(json_dumps(value))
    elif isinstance(value, set):
        log.info(json_dumps(list(value)))
    elif isinstance(value, BaseModel):
        log.info(json_dumps(value.model_dump(mode="json")))
    elif isinstance(value, str):
        for line in value.splitlines():
            log.info(line)
    else:
        log.info(str(value))
    log.info("::endgroup::")


def lst(lst: list) -> str:
    """Petit utilitaire pour afficher une liste"""
    return ", ".join([str(x) for x in lst])


def preview_dict_subsets(d: dict, key_pattern: str) -> None:
    """To visualize subsets of large dicts more easily"""
    for key, value in d.items():
        if re.search(key_pattern, key):
            preview(f"config.{key}", value)


def preview_df_as_markdown(label: str, df: pd.DataFrame, groupby=None) -> None:
    """Variation de la preview pour une dataframe de manière à
    obtenir une table lisible. On ne filtre pas la df ici, c'est
    à l'appelant de décider (ex: this("me",df.head(10))

    groupby: permet par exemple de grouper la df en sous df pour
    l'affichage du clustering
    """
    size = size_info_get(df)
    log = logger_get()
    log.info(f"::group::📦 {label}: taille={size}, 🔽 Cliquer pour révéler la table 🔽")
    # Displaying 1 markdown table per group
    if groupby:
        cols_groupby = [groupby] if isinstance(groupby, str) else groupby
        cols_other = [col for col in df.columns if col not in cols_groupby]
        for group, group_df in df.groupby(cols_groupby):
            df_md = group_df[cols_other].to_markdown(index=False)
            log.info(f"\n\n📦 GROUP: {lst(cols_groupby)}={lst(group)}\n\n{df_md}\n\n")
    else:
        # No grouping, display the whole dataframe
        # But if more than 1K line need to split or it causes big
        # performance issue in Airflow logs
        limit = 500
        split = int(limit / 2)
        if len(df) > limit:
            log.info(f"> {limit} lignes: affichage des {split} lignes de début/fin")
            log.info(f"\n {split} début:\n" + df.head(split).to_markdown(index=False))
            log.info(f"\n {split} fin:\n" + df.tail(split).to_markdown(index=False))
        else:
            log.info("\n" + df.to_markdown(index=False))
    log.info("::endgroup::")


def banner_string(message: str) -> str:
    """Retourne une bannière après retour
    de ligne pour qu'elle se retrouve visible tout à gauche
    (et pas en fin de ligne)"""
    return f"""

{'=' * 80}
{message}
{'=' * 80}
    """


def progress_string(count: int, total: int) -> str:
    """Returns a string with the progress of a task, in the form:
    "current / total (percentage %) ######" where # is proportional
    to percentage"""
    percent = math.ceil((count / total) * 100) if total > 0 else 0
    bars = "#" * (percent // 2)
    return f"{count} / {total} ({percent} %) {bars}"
