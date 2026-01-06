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
    apply_include_sources_to_parents: bool,
    include_acteur_type_ids: list[int],
    apply_include_acteur_types_to_parents: bool,
    include_only_if_regex_matches_nom: str | None,
    apply_include_only_if_regex_matches_nom_to_parents: bool,
    include_if_all_fields_filled: list[str],
    apply_include_if_all_fields_filled_to_parents: bool,
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

    # --------------------------------
    # 1) Select orphans
    # --------------------------------
    logging.info(log.banner_string("Sélection des orphelins"))
    fields = fields_protected + fields_transformed + include_if_all_fields_filled
    df_orphans, sql = cluster_acteurs_read_orphans(
        fields=fields,
        include_source_ids=include_source_ids,
        include_acteur_type_ids=include_acteur_type_ids,
        include_only_if_regex_matches_nom=include_only_if_regex_matches_nom,
        include_if_all_fields_filled=include_if_all_fields_filled,
    )
    log.preview("requête SQL utilisée", sql)
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
    # 2) Select parents only
    # --------------------------------
    logging.info(log.banner_string("Sélection des parents"))

    df_parents, sql_parents = cluster_acteurs_read_parents(
        fields=fields,
        include_source_ids=(
            include_source_ids if apply_include_sources_to_parents else []
        ),
        include_acteur_type_ids=(
            include_acteur_type_ids if apply_include_acteur_types_to_parents else []
        ),
        include_only_if_regex_matches_nom=(
            include_only_if_regex_matches_nom
            if apply_include_only_if_regex_matches_nom_to_parents
            else None
        ),
        include_if_all_fields_filled=(
            include_if_all_fields_filled
            if apply_include_if_all_fields_filled_to_parents
            else []
        ),
    )
    log.preview("requête SQL utilisée pour les parents", sql_parents)
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
