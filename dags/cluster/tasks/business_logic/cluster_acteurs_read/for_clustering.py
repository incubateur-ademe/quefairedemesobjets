import logging

import numpy as np
import pandas as pd
from cluster.tasks.business_logic.misc.df_sort import df_sort
from utils import logging_utils as log
from utils.django import (
    django_model_queryset_generate,
    django_model_queryset_to_df,
    django_model_queryset_to_sql,
    django_setup_full,
)

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
    logger.info(log.banner_string("Sélection des orphelins"))
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
    logger.info(log.banner_string("Sélection des parents"))

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
    logger.info(log.banner_string("Fusion parents + orphelins"))
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


def cluster_acteurs_read_parents(
    fields: list[str],
    include_source_ids: list[int] = [],
    include_acteur_type_ids: list[int] = [],
    include_only_if_regex_matches_nom: str | None = None,
    include_if_all_fields_filled: list[str] = [],
) -> tuple[pd.DataFrame, str]:
    """Reading parents from DB (acteurs with children pointing to them)."""
    return _cluster_acteurs_read_base(
        fields=fields,
        include_source_ids=include_source_ids,
        include_acteur_type_ids=include_acteur_type_ids,
        include_only_if_regex_matches_nom=include_only_if_regex_matches_nom,
        include_if_all_fields_filled=include_if_all_fields_filled,
        est_parent=True,
    )


def _cluster_acteurs_read_base(
    fields: list[str],
    include_source_ids: list[int],
    include_acteur_type_ids: list[int],
    include_only_if_regex_matches_nom: str | None,
    include_if_all_fields_filled: list[str],
    est_parent: bool,
) -> tuple[pd.DataFrame, str]:
    """
    Reading actors from DB (orphans or parents).

    We do 2 steps:
    1) Django queryset: filter data from request
    2) Transform and enrich DataFrame

    Args:
        ➕ include_source_ids (list[int]): sources to include

        ➕ include_acteur_type_ids (list[int]): actor types to include

        ➕ include_only_if_regex_matches_nom (str): actors included if name matches
            If no regex = no filtering = all names are included

        ➕ include_if_all_fields_filled (list[str]): actors included
            If ALL fields are filled

    Returns:
        tuple[pd.DataFrame, str]: DataFrame of actors and SQL query used
    """
    from qfdmo.models import ActeurType, Source, VueActeur

    # Remove duplicates
    fields = list(set(fields))

    # -----------------------------------
    # 1) Django queryset
    # -----------------------------------
    query = django_model_queryset_generate(VueActeur, include_if_all_fields_filled)
    if include_source_ids:
        query = query.filter(sources__id__in=include_source_ids)
    if include_acteur_type_ids:
        query = query.filter(acteur_type_id__in=include_acteur_type_ids)
    if include_only_if_regex_matches_nom:
        query = query.filter(nom__iregex=include_only_if_regex_matches_nom)
    query = query.filter(parent_id__isnull=True)
    query = query.filter(est_parent=est_parent)

    # Prefetch sources to avoid N+1 queries
    if est_parent:
        query = query.prefetch_related("sources")

    # -----------------------------------
    # 2) DataFrame
    # -----------------------------------
    sql = django_model_queryset_to_sql(query)
    df = django_model_queryset_to_df(query, fields)

    if df.empty:
        return df, sql

    # -----------------------------------
    # Format and add useful fields
    # -----------------------------------
    df = df.replace({"": None, np.nan: None})
    mapping_source_codes_by_ids = {x.id: x.code for x in Source.objects.all()}
    mapping_acteur_type_codes_by_ids = {x.id: x.code for x in ActeurType.objects.all()}
    df["source_code"] = df["source_id"].map(mapping_source_codes_by_ids)
    df["acteur_type_code"] = df["acteur_type_id"].map(mapping_acteur_type_codes_by_ids)

    # Calculate source_codes according to type
    if est_parent:
        # For parents, we get all source codes from the prefetched queryset
        source_codes_by_parent_identifiant_unique = {
            parent.identifiant_unique: tuple(
                parent.sources.values_list("code", flat=True)
            )
            for parent in query
        }
        df["source_codes"] = df["identifiant_unique"].map(
            pd.Series(source_codes_by_parent_identifiant_unique)
        )
    else:
        # For orphans, we simply create a list with the unique source code
        df["source_codes"] = df["source_code"].apply(lambda x: [x])

    return df, sql
