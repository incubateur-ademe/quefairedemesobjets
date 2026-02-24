import pandas as pd

ID = "identifiant_unique"
COUNT_CLUSTERS = "1) 📦 Nombre Clusters Proposés"
COUNT_CLUSTERS_CURRENT = "2) 📦 Nombre Clusters Existants"
COUNT_CLUSTERS_NET = "3) 📦 Nombre Clusters Net"
COUNT_ACTEURS = "4) 🎭 Nombre Acteurs Total"
COUNT_ACTEURS_CURRENT = "5) 🎭 Nombre Acteurs Déjà Clusterisés"
COUNT_ACTEURS_NEW = "6) 🎭 Nombre Acteurs Nouvellement Clusterisés"


def df_metadata_get(df_clusters: pd.DataFrame) -> dict:
    """Génère des statistiques sur les clusters, à noter que
    la fonction peut être utilisée dans 2 contextes:
     - cohorte: df_clusters cotient plusieurs clusters
     - suggestion: df_clusters contient un seul cluster, auquel cas
        les champs nombre_cluster* sont à 1 et pas utiles mais
        cela nous évite de faire une fonction spécifique

    Args:
        df_clusters (pd.DataFrame): les clusters à analyser

    Returns:
        dict: les metadata générées
    """
    df = df_clusters
    meta = {}
    meta[COUNT_CLUSTERS] = df["cluster_id"].nunique()
    # Chaque parent existant est de fait un cluster existant
    meta[COUNT_CLUSTERS_CURRENT] = df[df["nombre_enfants"] > 0][ID].nunique()
    meta[COUNT_CLUSTERS_NET] = meta[COUNT_CLUSTERS] - meta[COUNT_CLUSTERS_CURRENT]
    meta[COUNT_ACTEURS_CURRENT] = int(df["nombre_enfants"].sum())
    meta[COUNT_ACTEURS] = df[ID].nunique() - meta[COUNT_CLUSTERS_CURRENT]
    meta[COUNT_ACTEURS_NEW] = meta[COUNT_ACTEURS] - meta[COUNT_ACTEURS_CURRENT]

    return meta
