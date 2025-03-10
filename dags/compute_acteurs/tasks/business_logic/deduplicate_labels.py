import pandas as pd
from compute_acteurs.tasks.transform.merge_and_deduplicate import (
    deduplicate_acteurs_many2many_relationship,
)


def deduplicate_labels(
    df_children: pd.DataFrame,
    df_labels: pd.DataFrame,
):
    return deduplicate_acteurs_many2many_relationship(
        df_children,
        df_labels,
        "labelqualite_id",
    )
