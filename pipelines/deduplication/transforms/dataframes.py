from typing import List

import numpy as np
import pandas as pd
from rich import print


def dfs_merge_coalesce(dfs: List[pd.DataFrame], merge_on: str) -> pd.DataFrame:
    """
    Merge et coalesce des dataframes

    Args:
        dfs (List[pd.DataFrame]): Liste de dataframes à merger
        merge_on (str): Colonne sur laquelle merger

    Returns:
        pd.DataFrame: nouvelle dataframe mergée
    """
    if len(dfs) < 2:
        raise ValueError("dfs_merge_coalesce only works with 2+ dataframes")
    if any(not isinstance(df, pd.DataFrame) for df in dfs):
        raise ValueError("All elements of dfs must be pandas DataFrames")
    if any(merge_on not in df.columns for df in dfs):
        raise ValueError(f"Column {merge_on} not found in all dataframes")
    # S'assurer qu'on a bien des None pour que combine_first fonctionne
    # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.combine_first.html
    # "Update null elements"
    for i, df in enumerate(dfs):
        dfs[i] = df.replace({None: np.nan})
    for i, df in enumerate(dfs):
        print(f"df {i=}", f"{df.columns.tolist()=}")
        if i == 0:
            merged = df.set_index(merge_on)
        else:
            merged = merged.combine_first(df.set_index(merge_on))
            # On s'assure que le merge ne ré-introduit pas de NaN
            merged = merged.replace({np.nan: None})
    return df.reset_index().replace({np.nan: None})


def df_mapping_one_to_one(label: str, df: pd.DataFrame, col1: str, col2: str) -> dict:
    """Création d'un mapping de col1 -> col2 à partir d'un DataFrame

    Args:
        label (str): label pour affichage
        df (pd.DataFra!e): DataFrame
        col1: colonne 1 (clé)
        col2: colonne 2 (valeur)

    Returns:
        dict: mapping col1 -> col2
    """
    print(f"MAPPING 1->1: '{label}' sur {df.shape=}: {col1=}, {col2=}")

    # Vérifications
    dups = df[df.duplicated(subset=col1, keep=False)]
    if not dups.empty:
        raise ValueError(f"{label}: doublons sur {col1}")
    if not df[df[col1].isnull()].empty:
        raise ValueError(f"{label}: nulls sur {col1}")
    if not df[df[col2].isnull()].empty:
        raise ValueError(f"{label}: nulls sur {col2}")
    # Création du mapping
    mapping = df.set_index(col1)[col2].to_dict()
    samples = {k: mapping[k] for k in list(mapping.keys())[:3]}
    print(f"MAPPING 1->1: {label} - taille: {len(mapping)=}")
    print(f"MAPPING 1->1: {label} - samples: {samples=}")
    return mapping


def df_mapping_one_to_many(label, df, col1, col2) -> dict:
    """Création d'un mapping de col1 -> [col2] à partir d'un DataFrame"""
    print(f"MAPPING 1->MANY: '{label}' sur {df.shape=}: {col1=}, {col2=}")

    # Vérifications
    if not df[df[col1].isnull()].empty:
        raise ValueError(f"{label}: nulls sur {col1}")
    if not df[df[col2].isnull()].empty:
        raise ValueError(f"{label}: nulls sur {col2}")
    mapping = df.groupby(col1)[col2].apply(list).to_dict()
    samples = {k: mapping[k] for k in list(mapping.keys())[:3]}
    print(f"MAPPING 1->MANY: {label} - taille: {len(mapping)=}")
    print(f"MAPPING 1->MANY: {label} - samples: {samples=}")
    return mapping
