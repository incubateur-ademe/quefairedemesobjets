import pandas as pd
from compute_acteurs.tasks.transform.merge_and_deduplicate import (
    deduplicate_acteurs_many2many_relationship,
)


def deduplicate_acteur_services(
    df_children: pd.DataFrame,
    df_acteur_services: pd.DataFrame,
):
    return deduplicate_acteurs_many2many_relationship(
        df_children,
        df_acteur_services,
        "acteurservice_id",
    )
