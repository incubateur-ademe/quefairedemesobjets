import logging

import pandas as pd

logger = logging.getLogger(__name__)


def df_add_original_columns(
    df_clusters: pd.DataFrame,
    df_original: pd.DataFrame,
) -> pd.DataFrame:
    """Utilitaire pour réenrichir un df de clusters
    avec les données manquantes qui étaient présentent
    dans le df original

    Raison: dans le clustering on veut pas se trimballer
    toute la donnée (trop lourd, si on utilise des fonctions
    de groupby il faut gérer les aggregations, etc.), donc
    c'est normal qu'en sortie de clustering on ait perdu
    les champs non-clustering, qu'on vient rajouter à posteriori
    """
    cols_add = [x for x in df_original.columns if x not in df_clusters.columns]
    logger.info(f"Colonnes à rajouter: {cols_add}")
    cols = ["identifiant_unique"] + cols_add
    return df_clusters.merge(df_original[cols], on="identifiant_unique", how="left")
