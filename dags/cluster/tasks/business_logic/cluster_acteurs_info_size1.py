import pandas as pd


def cluster_info_size1_exact_fields(
    df: pd.DataFrame, cluster_fields_exact: list[str]
) -> dict[str, dict]:
    """Fonction qui retourne les clusters de taille 1 quand on applique du
    groupage sur les champs à match exact.

    Args:
        df (pd.DataFrame): Le DataFrame contenant les acteurs
        cluster_fields_exact (list[str]): Les champs sur lesquels
        on fait le groupage exact.

    Returns:
        dict[str, dict]: Un dictionnaire avec les champs groupés en clé
        et en valeur le nombre de clusters de taille 1 et un échantillon
    """

    # Convertit la liste de tous les champs en une liste de listes de champs
    # de taille croissante, pour mieux comprendre à partir de quel champ
    # on commence à avoir des clusters de taille 1.
    # ["a","b","c"] => [ ["a"], ["a","b"], ["a","b","c"]]
    fields_groups = [
        cluster_fields_exact[:i] for i in range(1, len(cluster_fields_exact) + 1)
    ]

    results = {}
    for fields_group in fields_groups:
        # On fait un groupby sur les champs de fields_group
        # et on compte le nombre d'occurrences
        # On garde les clusters de taille 1
        clusters = df.groupby(fields_group).size().reset_index(name="count")
        size1 = clusters[clusters["count"] == 1]
        # Trie par ordre croissant des valeurs de groupage pour faciliter
        # la revue métier
        size1 = size1.sort_values(by=fields_group)
        results[" + ".join(fields_group)] = {
            "count": len(size1),
            "sample": size1,
        }
    return results
