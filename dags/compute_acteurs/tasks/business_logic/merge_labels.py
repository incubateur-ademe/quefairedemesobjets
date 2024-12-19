import pandas as pd
from compute_acteurs.tasks.transform.merge_and_deduplicate import (
    merge_acteurs_many2many_relationship,
)


def merge_labels(
    df_acteur_labels: pd.DataFrame,
    df_revisionacteur_labels: pd.DataFrame,
    df_revisionacteur: pd.DataFrame,
):

    return merge_acteurs_many2many_relationship(
        df_link_with_acteur=df_acteur_labels,
        df_link_with_revisionacteur=df_revisionacteur_labels,
        df_revisionacteur=df_revisionacteur,
    )
