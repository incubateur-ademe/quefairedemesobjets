import pandas as pd
from shared.tasks.business_logic import normalize


def cluster_acteurs_normalize(
    df: pd.DataFrame,
    normalize_fields_basic: list[str],
    normalize_fields_no_words_size1: list[str],
    normalize_fields_no_words_size2_or_less: list[str],
    normalize_fields_no_words_size3_or_less: list[str],
    normalize_fields_order_unique_words: list[str],
) -> pd.DataFrame:
    """Fonction qui normalise les champs à match exact pour les acteurs.

    Args:
        df (pd.DataFrame): Le DataFrame contenant les acteurs
        cluster_fields_exact (list[str]): Les champs sur lesquels
    """
    # Si aucun champ spécifié, on applique la normalisation basique à tous les champs
    if not normalize_fields_basic:
        normalize_fields_basic = df.columns.tolist()
    for field in normalize_fields_basic:
        df[field] = df[field].map(normalize.string_basic)

    for field in normalize_fields_no_words_size1:
        df[field] = df[field].map(lambda x: normalize.string_remove_small_words(x, 1))

    for field in normalize_fields_no_words_size2_or_less:
        df[field] = df[field].map(lambda x: normalize.string_remove_small_words(x, 2))

    for field in normalize_fields_no_words_size3_or_less:
        df[field] = df[field].map(lambda x: normalize.string_remove_small_words(x, 3))

    # Si aucun champ spécifié, on applique la normalisation des mots
    # dans l'ordre/unique à tous les champs
    if not normalize_fields_order_unique_words:
        normalize_fields_order_unique_words = df.columns.tolist()
    for field in normalize_fields_order_unique_words:
        df[field] = df[field].map(normalize.string_order_unique_words)

    # TODO: à voir si on garde cette colonne: elle nous a servi au début
    # de la construction de l'algorithme de clustering quand on construisait
    # nos tests et qu'on voulait une façon fiable de savoir quelles lignes
    # avaient été clusterisées (indépendamment de l'ordre, filtrage, etc.)
    # Maintenant qu'on se rapproche de la prod, on pourrait décider de ré-écrire
    # les tests en se basant sur identifiant_unique et ainsi supprimer __index_src
    df["__index_src"] = range(1, len(df) + 1)

    return df
