import pandas as pd


def cluster_acteurs_metadata(df_clusters: pd.DataFrame) -> dict:
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
    # TODO: on pourrait surement définir un fichier de traduction avec
    # les clefs en anglais et les valeurs en français, pour l'instant
    # je mets la meta en FR (pour métier) de façon à toute afficher
    # en dynamique dans Django Admin sans avoir à se soucier de tradu là bas
    meta["nombre_clusters"] = df["cluster_id"].nunique()
    meta["nombre_clusters_existants"] = df[df["is_parent_current"]][
        "cluster_id"
    ].nunique()
    meta["nombre_clusters_nouveaux"] = (
        meta["nombre_clusters"] - meta["nombre_clusters_existants"]
    )
    meta["nombre_acteurs"] = df["id"].nunique()
    meta["nombre_acteurs_deja_parent"] = df[df["is_parent_current"]]["id"].nunique()
    meta["nombre_acteurs_deja_enfant"] = df[df["parent_id"].notnull()]["id"].nunique()
    meta["nombre_acteurs_nouveau_enfant"] = (
        meta["nombre_acteurs"]
        - meta["nombre_acteurs_deja_enfant"]
        - meta["nombre_acteurs_deja_parent"]
    )

    return meta
