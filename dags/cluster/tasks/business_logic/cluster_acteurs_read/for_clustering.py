import logging

import numpy as np
import pandas as pd
from cluster.tasks.business_logic.cluster_acteurs_read.orphans import (
    cluster_acteurs_read_orphans,
)
from cluster.tasks.business_logic.cluster_acteurs_read.parents import (
    cluster_acteurs_read_parents,
)
from cluster.tasks.business_logic.misc.df_sort import df_sort
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def cluster_acteurs_read_for_clustering(
    include_source_ids: list[int],
    include_acteur_type_ids: list[int],
    include_only_if_regex_matches_nom: str | None,
    include_if_all_fields_filled: list[str],
    exclude_if_any_field_filled: list[str],
    include_parents_only_if_regex_matches_nom: str | None,
    fields_protected: list[str],
    fields_transformed: list[str],
) -> pd.DataFrame:
    """Reading from DB what is needed for clustering. Right now it is:
    - orphans
    - parents

    Because we only want to add to existing clusters.

    However in the future if we decide we want to
    re-cluster everything we might add to that:
    - children

    Hence the abstracted name "read_for_clustering"
    """

    from qfdmo.models import VueActeur

    # --------------------------------
    # 1) Sélection des orphelins
    # --------------------------------
    # Quels qu'ils soient (enfants ou parents) sur la
    # base de tous les critères d'inclusion/exclusion
    # fournis au niveau du DAG
    logging.info(log.banner_string("Sélection des orphelins"))
    df_orphans, query = cluster_acteurs_read_orphans(
        model_class=VueActeur,
        include_source_ids=include_source_ids,
        include_acteur_type_ids=include_acteur_type_ids,
        include_only_if_regex_matches_nom=include_only_if_regex_matches_nom,
        include_if_all_fields_filled=include_if_all_fields_filled,
        exclude_if_any_field_filled=exclude_if_any_field_filled,
        extra_dataframe_fields=fields_transformed,
    )
    log.preview("requête SQL utilisée", query)
    logger.info(f"# orphelins récupérées: {len(df_orphans)}")
    if df_orphans.empty:
        return df_orphans
    log.preview("# acteurs par source_code", df_orphans.groupby("source_code").size())
    log.preview(
        "# acteurs par acteur_type_code", df_orphans.groupby("acteur_type_code").size()
    )
    log.preview_df_as_markdown("acteurs sélectionnés", df_orphans)
    df_orphans = df_sort(df_orphans)

    # --------------------------------
    # 2) Sélection des parents uniquements
    # --------------------------------
    # Aujourd'hui (2025-01-27): la convention data veut qu'un parent
    # soit attribué une source NULL. Donc si le métier choisit de
    # clusteriser des sources en particulier à 1), on ne peut donc
    # jamais récupérer les parents potentiels pour le même type d'acteur
    # La logique ci-dessous vient palier à ce problème en sélectionnant
    # TOUS les parents des acteurs types sélectionnés, et en ignorant
    # les autres paramètres de sélection
    logging.info(log.banner_string("Sélection des parents"))
    df_parents = cluster_acteurs_read_parents(
        acteur_type_ids=include_acteur_type_ids,
        fields=fields_protected + fields_transformed,
        include_only_if_regex_matches_nom=include_parents_only_if_regex_matches_nom,
    )
    df_parents = df_sort(df_parents)
    log.preview_df_as_markdown("parents sélectionnés", df_parents)

    # --------------------------------
    # 3) Fusion acteurs + orphelins
    # --------------------------------
    logging.info(log.banner_string("Fusion parents + orphelins"))
    ids = set()
    ids.update(df_orphans["identifiant_unique"].values)
    ids.update(df_parents["identifiant_unique"].values)
    log.preview("IDs avant la fusion", ids)
    df = pd.concat([df_orphans, df_parents], ignore_index=True).replace({np.nan: None})
    df = df.drop_duplicates(subset="identifiant_unique", keep="first")
    df = df_sort(df)
    log.preview("IDs après la fusion", df["identifiant_unique"].tolist())
    log.preview_df_as_markdown("acteurs + parents sélectionnés", df)

    return df
