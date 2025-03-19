import pandas as pd


def cluster_exclude_intra_source(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    """
    Exclue les acteurs d'une même source (si il y en a) d'un cluster donné,
    en ne conservant qu'1 seul acteur par source

    Args:
        df (pd.DataFrame): DataFrame contenant les acteurs du cluster

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: 1er élément: DataFrame des acteurs
        conservés, 2ème élément: DataFrame des acteurs exclus
    """
    # Pour l'instant on contraint l'utilisation de cette fonction sur 1 seul cluster
    if not df["cluster_id"].nunique() == 1:
        raise ValueError("Fonction à utiliser sur 1 seul cluster")

    # Les acteurs parents n'ont pas de source_id, et donc ne sont pas concernés
    df_children = df[df["source_id"].notnull()]
    df_parents = df[df["source_id"].isnull()]

    # Pas de doublons de source -> on retourne le df d'origine
    if df_children["source_id"].nunique() == len(df_children):
        return df, None

    # Pour chaque source, on ne garde qu'un seul acteur
    # (pour l'instant on garde le premier)
    # TODO: améliorer avec les scores de similarité
    df_children_kept = df_children.groupby("source_id").first().reset_index()

    # Résultat final: acteurs conservés vs. exclus
    id = "id"
    df_kept = pd.concat([df_children_kept, df_parents], ignore_index=True)
    df_lost = df_children[~df_children[id].isin(df_kept[id])].reset_index(drop=True)

    return df_kept, df_lost
