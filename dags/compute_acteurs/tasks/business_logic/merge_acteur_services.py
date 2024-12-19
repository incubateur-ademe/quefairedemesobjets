import pandas as pd
from compute_acteurs.tasks.transform.merge_and_deduplicate import (
    merge_acteurs_many2many_relationship,
)


def merge_acteur_services(
    df_acteur_acteur_services: pd.DataFrame,
    df_revisionacteur_acteur_services: pd.DataFrame,
    df_revisionacteur: pd.DataFrame,
):

    return merge_acteurs_many2many_relationship(
        df_link_with_acteur=df_acteur_acteur_services,
        df_link_with_revisionacteur=df_revisionacteur_acteur_services,
        df_revisionacteur=df_revisionacteur,
    )
