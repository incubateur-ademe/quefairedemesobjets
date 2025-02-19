import pandas as pd
from cluster.config.constants import COL_INDEX_SRC
from shared.tasks.business_logic import normalize


def cluster_acteurs_normalize(
    df: pd.DataFrame,
    normalize_fields_basic: list[str],
    normalize_fields_no_words_size1: list[str],
    normalize_fields_no_words_size2_or_less: list[str],
    normalize_fields_no_words_size3_or_less: list[str],
    normalize_fields_order_unique_words: list[str],
) -> pd.DataFrame:
    """Fonction de normalisation de la df d'acteurs.

    Note: toute la logique de défault/métier est à gérer en amont
    dans la config pour construire les champs normalize_fields
    aux besoins.

    Args:
        df (pd.DataFrame): Le DataFrame contenant les acteurs
        cluster_fields_exact (list[str]): Les champs sur lesquels
    """
    for field in normalize_fields_basic:
        df[field] = df[field].map(normalize.string_basic)

    for field in normalize_fields_no_words_size1:
        df[field] = df[field].map(lambda x: normalize.string_remove_small_words(x, 1))

    for field in normalize_fields_no_words_size2_or_less:
        df[field] = df[field].map(lambda x: normalize.string_remove_small_words(x, 2))

    for field in normalize_fields_no_words_size3_or_less:
        df[field] = df[field].map(lambda x: normalize.string_remove_small_words(x, 3))

    for field in normalize_fields_order_unique_words:
        df[field] = df[field].map(normalize.string_order_unique_words)

    # TODO: à voir si on garde cette colonne: elle nous a servi au début
    # de la construction de l'algorithme de clustering quand on construisait
    # nos tests et qu'on voulait une façon fiable de savoir quelles lignes
    # avaient été clusterisées (indépendamment de l'ordre, filtrage, etc.)
    # Maintenant qu'on se rapproche de la prod, on pourrait décider de ré-écrire
    # les tests en se basant sur identifiant_unique et ainsi supprimer __index_src
    df[COL_INDEX_SRC] = range(1, len(df) + 1)

    # TODO: investiguer pourquoi le type du champ ci-dessous bascule de int->str
    # pendant la norma alors que le champ n'est pas manipulé, en dessous = quick fix
    if "nombre_enfants" in df.columns:
        df["nombre_enfants"] = df["nombre_enfants"].astype(int)

    return df
