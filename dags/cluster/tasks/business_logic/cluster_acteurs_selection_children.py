import numpy as np
import pandas as pd
from utils.django import django_setup_full

django_setup_full()
from qfdmo.models.acteur import ActeurStatus  # noqa: E402
from qfdmo.models.acteur import RevisionActeur  # noqa: E402


def cluster_acteurs_selection_children(
    parent_ids: list[str],
    fields_to_include: list[str],
) -> pd.DataFrame:
    """Sélectionne les enfants des parents donnés

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
    return pd.DataFrame(children, dtype="object").replace({np.nan: None})
