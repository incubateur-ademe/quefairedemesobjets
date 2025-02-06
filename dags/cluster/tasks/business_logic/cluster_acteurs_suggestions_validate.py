from logging import getLogger

import pandas as pd

logger = getLogger(__name__)


def raise_if_df_not_empty(df: pd.DataFrame, error) -> None:
    """Petit utilitaire pour éviter répétition dans fonction
    de validation"""
    if not df.empty:
        logger.error(df.to_markdown(index=False))
        raise ValueError(error)


def cluster_acteurs_suggestions_validate(df_clusters: pd.DataFrame) -> None:
    """Validation des propositions de clusters

    Args:
        df_clusters (pd.DataFrame): les clusters à valider
    """
    df = df_clusters

    # ------------------------------------
    # Validations sur acteurs individuels
    # ------------------------------------
    # On ne tolère aucun acteur non-ACTIF: si on fait bien notre
    # travail, on doit partir des acteurs actifs tels qu'affichés
    # sur la carte et donc jamais on doit se retrouver avec des non-actifs
    df_non_actifs = df[df["statut"].str.lower() != "actif"]
    raise_if_df_not_empty(df_non_actifs, "Clusters avec acteurs non-ACTIF")
    logger.info("100% acteurs actifs: 🟢")

    # Chaque acteur doit n'être définis qu'une seule fois
    df_multiple_clusters = df.groupby("identifiant_unique").filter(lambda x: len(x) > 1)
    raise_if_df_not_empty(df_multiple_clusters, "Acteurs définis plusieurs fois")
    logger.info("100% acteurs définis 1 seule fois: 🟢")

    # ------------------------------------
    # Validations sur clusters entiers
    # ------------------------------------
    # Les clusters doivent avoir au moins 2 acteurs
    df_less_than_2 = df.groupby("cluster_id").filter(lambda x: len(x) < 2)
    raise_if_df_not_empty(df_less_than_2, "Clusters avec moins de 2 acteurs")
    logger.info("100% clusters taille 2+: 🟢")

    # Les IDs des clusters doivent être ordonnées: sinon c'est peut être qu'on
    # a des collisions ou des problèmes de logique, on préfère être sûr
    cluster_ids_not_ordered = not df["cluster_id"].is_monotonic_increasing
    if cluster_ids_not_ordered:
        raise ValueError("Cluster IDs non ordonnés de manière croissante")
    logger.info("100% cluster IDs ordonnés: 🟢")
