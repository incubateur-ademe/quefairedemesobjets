import pandas as pd
from cluster.config.constants import COL_PARENT_DATA_NEW
from utils.django import django_setup_full

django_setup_full()


def df_sort(
    df: pd.DataFrame,
    cluster_fields_exact: list[str] = [],
    cluster_fields_fuzzy: list[str] = [],
) -> pd.DataFrame:
    """Utility to help us sort dataframes in a consistent way
    throught clustering pipeline despite them having potentially
    different columns"""

    from data.models.change import (
        COL_CHANGE_ENTITY_TYPE,
        COL_CHANGE_MODEL_NAME,
        COL_CHANGE_ORDER,
        COL_CHANGE_REASON,
    )

    # SORTING ROWS: by what makes clusters logical
    sort_rows = ["cluster_id", COL_CHANGE_ORDER]
    if cluster_fields_exact or cluster_fields_fuzzy:
        sort_rows += [COL_CHANGE_ENTITY_TYPE, "source_code", "acteur_type_code"]
    sort_rows += [x for x in cluster_fields_exact if x not in sort_rows]
    sort_rows += [x for x in cluster_fields_fuzzy if x not in sort_rows]
    sort_rows += [
        x for x in ["code_postal", "ville", "adresse", "nom"] if x not in sort_rows
    ]
    sort_rows = [x for x in sort_rows if x in df.columns]
    sort_rows += [
        x for x in df.columns if x not in cluster_fields_exact and x not in sort_rows
    ]
    df = df.sort_values(by=sort_rows)[sort_rows]

    # SORTING COLUMNS: by what makes sense for debugging
    sort_cols = [
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
    sort_cols = [x for x in sort_cols if x in df.columns]
    sort_cols += [x for x in cluster_fields_exact if x not in sort_cols]
    sort_cols += [x for x in cluster_fields_fuzzy if x not in sort_cols]
    sort_cols += [x for x in df.columns if x not in sort_cols]

    return df[sort_cols]
