import pandas as pd
from utils.django import django_model_queryset_to_df, django_setup_full

django_setup_full()
from qfdmo.models import ActeurType, DisplayedActeur  # noqa: E402
from qfdmo.models.acteur import ActeurStatus  # noqa: E402


def cluster_acteurs_selection_acteur_type_parents(
    acteur_type_ids: list[int],
    fields: list[str],
) -> pd.DataFrame:
    """Sélectionne tous les parents des acteurs types donnés,
    pour pouvoir notamment permettre de clusteriser avec
    ces parents existant indépendemment des critères de sélection
    des autres acteurs qu'on cherche à clusteriser (ex: si on cherche
    à clusteriser les acteurs commerce de source A MAIS en essayant
    de rattacher au maximum avec tous les parents commerce existants)"""

    # Petite validation (on ne fait pas confiance à l'appelant)
    ids_in_db = list(ActeurType.objects.values_list("id", flat=True))
    ids_invalid = set(acteur_type_ids) - set(ids_in_db)
    if ids_invalid:
        raise ValueError(f"acteur_type_ids {ids_invalid} pas trouvés en DB")

    # On récupère les parents des acteurs types donnés
    # qui sont censés être des acteurs sans source
    parents = DisplayedActeur.objects.filter(
        acteur_type__id__in=acteur_type_ids,
        statut=ActeurStatus.ACTIF,
        source__id__isnull=True,
    )

    return django_model_queryset_to_df(parents, fields)
