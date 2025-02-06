import pandas as pd


def cluster_acteurs_df_sort(
    df: pd.DataFrame,
    cluster_fields_exact: list[str] = [],
    cluster_fields_fuzzy: list[str] = [],
) -> pd.DataFrame:
    """Fonction de tri d'une dataframe acteurs
    pour favoriser la visualisation des clusters.

    La fonction peut fonctionner sur n'importe quel
    état d'une dataframe acteurs (sélection, normalisation,
    clusterisation).

    De fait elle est utilisée tout au long du DAG
    airflow de clustering pour mieux visualiser la
    construction des clusters au fur et à mesure des tâches.

    Args:
        df (pd.DataFrame): DataFrame acteurs
        cluster_fields_exact (list[str], optional): Liste des champs exacts
        pour le clustering. Defaults to [].
        cluster_fields_fuzzy (list[str], optional): Liste des champs flous
        pour le clustering. Defaults to [].

    Returns:
        pd.DataFrame: DataFrame acteurs triée
    """

    # On construit une liste de champs de tri
    # avec des champs par défauts (ex: cluster_id)
    # et des champs spécifiés dans la config du DAG
    sort_ideal = ["cluster_id"]  # la base du clustering

    # pour déceler des erreurs de clustering rapidement (ex: intra-source)
    # mais on le met pas pour les étapes de sélection et normalisation
    # car cela casse notre ordre (on a pas de cluster_id et donc
    # on préfère par sémantique business que des codes)
    if cluster_fields_exact or cluster_fields_fuzzy:
        sort_ideal += ["source_code", "acteur_type_code"]
    sort_ideal += [x for x in cluster_fields_exact if x not in sort_ideal]
    sort_ideal += [x for x in cluster_fields_fuzzy if x not in sort_ideal]
    # défaut quand on n'a pas de champs de clustering (étape de sélection)
    sort_ideal += [
        x for x in ["code_postal", "ville", "adresse", "nom"] if x not in sort_ideal
    ]

    # Puis on construit la liste actuelle des champs de tri
    # vs. la réalité des champs présents dans la dataframe
    # en prenant "au mieux" dans l'ordre idéale et en rajoutant
    # ce qui reste de la df
    sort_actual = [x for x in sort_ideal if x in df.columns]
    sort_actual += [
        x for x in df.columns if x not in cluster_fields_exact and x not in sort_actual
    ]
    return df.sort_values(by=sort_actual, ascending=True)[sort_actual]
