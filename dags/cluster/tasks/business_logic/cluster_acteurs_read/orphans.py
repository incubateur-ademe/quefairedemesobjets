import pandas as pd
from cluster.tasks.business_logic.cluster_acteurs_read._common import (
    _cluster_acteurs_read_base,
)
from utils.django import django_setup_full

django_setup_full()


def cluster_acteurs_read_orphans(
    fields: list[str],
    include_source_ids: list[int],
    include_acteur_type_ids: list[int],
    include_only_if_regex_matches_nom: str | None,
    include_if_all_fields_filled: list[str],
) -> tuple[pd.DataFrame, str]:
    """
    Reading orphans from DB
    (acteurs not pointing to parents and which aren't parents).
    """
    return _cluster_acteurs_read_base(
        fields=fields,
        include_source_ids=include_source_ids,
        include_acteur_type_ids=include_acteur_type_ids,
        include_only_if_regex_matches_nom=include_only_if_regex_matches_nom,
        include_if_all_fields_filled=include_if_all_fields_filled,
        est_parent=False,
    )
