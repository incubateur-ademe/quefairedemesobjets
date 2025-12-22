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
    """Normalization of acteurs"""

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

    return df
