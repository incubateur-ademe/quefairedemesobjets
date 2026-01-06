from logging import getLogger

import pandas as pd
from utils.django import django_setup_full

django_setup_full()

logger = getLogger(__name__)


def raise_if_df_not_empty(df: pd.DataFrame, error) -> None:
    """Little utility for our validation"""
    if not df.empty:
        logger.error(df.to_markdown(index=False))
        raise ValueError(error)


def cluster_acteurs_clusters_validate(df_clusters: pd.DataFrame) -> None:
    """Validate prepared clusters"""

    df = df_clusters

    # We should never cluster INACTIVE acteurs
    # df_non_actifs = df[df["statut"].str.upper() != ActeurStatus.ACTIF.upper()]
    # raise_if_df_not_empty(df_non_actifs, "Clusters avec acteurs non-ACTIF")
    # logger.info("100% acteurs actifs: 🟢")

    # There should be no duplicate acteurs
    df_multiple_clusters = df.groupby("identifiant_unique").filter(lambda x: len(x) > 1)
    raise_if_df_not_empty(df_multiple_clusters, "Acteurs définis plusieurs fois")
    logger.info("100% acteurs définis 1 seule fois: 🟢")

    # Clusters must be of size 2+
    df_less_than_2 = df.groupby("cluster_id").filter(lambda x: len(x) < 2)
    raise_if_df_not_empty(df_less_than_2, "Clusters avec moins de 2 acteurs")
    logger.info("100% clusters taille 2+: 🟢")

    # Cluster IDs should be ordered, else it's a potential sign of a bug
    cluster_ids_not_ordered = not df["cluster_id"].is_monotonic_increasing
    if cluster_ids_not_ordered:
        raise ValueError("Cluster IDs non ordonnés de manière croissante")
    logger.info("100% cluster IDs ordonnés: 🟢")
