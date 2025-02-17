import numpy as np
import pandas as pd
from utils.django import django_setup_full

django_setup_full()


def cluster_acteurs_read_children(
    parent_ids: list[str],
    fields_to_include: list[str],
) -> pd.DataFrame:
    from data.models.change import COL_CHANGE_ENTITY_TYPE, ENTITY_ACTEUR_REVISION
    from qfdmo.models.acteur import ActeurStatus, RevisionActeur

    """Reading children from DB (acteurs already pointing to parents).

    Args:
        parent_ids (list[str]): les identifiants des parents
        fields_to_include (list[str]): les champs à inclure dans le résultat

    Returns:
        pd.DataFrame: les enfants
    """
    children = [
        {field: getattr(x, field) for field in fields_to_include}
        for x in RevisionActeur.objects.filter(parent__in=parent_ids).filter(
            statut=ActeurStatus.ACTIF
        )
    ]
    df = pd.DataFrame(children, dtype="object").replace({np.nan: None})
    # If children are pointing to a parent it means they
    # received an update and thus are necessarily in revision
    df[COL_CHANGE_ENTITY_TYPE] = ENTITY_ACTEUR_REVISION
    return df
