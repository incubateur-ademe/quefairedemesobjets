import pandas as pd
from cluster.config.constants import COL_INDEX_SRC, COL_PARENT_DATA_NEW
from utils.django import django_setup_full

django_setup_full()


def df_sort(
    df: pd.DataFrame,
    cluster_fields_exact: list[str] = [],
    cluster_fields_fuzzy: list[str] = [],
) -> pd.DataFrame:
    """Fonction de tri des lignes & colonnes d'un df d'acteurs:
     - lignes: on favorise le groupement sémantique (ex: même ville)
     - colonnes: on favorise le debug métier (ex: identifiants)

    La fonction peut fonctionner sur n'importe quel
    état d'un df acteurs (sélection, normalisation,
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
        pd.DataFrame: DataFrame triée
    """

    from data.models.change import (
        COL_CHANGE_ENTITY_TYPE,
        COL_CHANGE_MODEL_NAME,
        COL_CHANGE_ORDER,
        COL_CHANGE_REASON,
    )

    sort_ideal = ["cluster_id", COL_CHANGE_ORDER]  # la base du clustering

    # pour déceler des erreurs de clustering rapidement (ex: intra-source)
    # mais on le met pas pour les étapes de sélection et normalisation
    # car cela casse notre ordre (on a pas de cluster_id et donc
    # on préfère par sémantique business que des codes)
    if cluster_fields_exact or cluster_fields_fuzzy:
        sort_ideal += [COL_CHANGE_ENTITY_TYPE, "source_code", "acteur_type_code"]
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
    df = df.sort_values(by=sort_actual, ascending=True)[sort_actual]

    # -----------------------------------------------
    # Tri des colonnes
    # -----------------------------------------------
    cols_ideal = [
        "cluster_id",
        "identifiant_unique",
        "statut",
        COL_CHANGE_ENTITY_TYPE,
        COL_CHANGE_MODEL_NAME,
        COL_CHANGE_REASON,
        COL_CHANGE_ORDER,
        "acteur_type_code",
        COL_PARENT_DATA_NEW,
    ]
    cols_last = [COL_INDEX_SRC]
    cols = [x for x in cols_ideal if x in df.columns]
    cols += [x for x in cluster_fields_exact if x not in cols]
    cols += [x for x in cluster_fields_fuzzy if x not in cols]
    cols += [x for x in df.columns if x not in cols]
    # Moving cols_last which are present to end
    cols = [x for x in cols if x not in cols_last] + [x for x in cols_last if x in cols]
    return df[cols]
