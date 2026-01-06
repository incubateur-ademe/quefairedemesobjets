import numpy as np
import pandas as pd
from utils.django import (
    django_model_queryset_generate,
    django_model_queryset_to_df,
    django_model_queryset_to_sql,
    django_setup_full,
)

django_setup_full()


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
        if est_parent:
            query = query.filter(sources__id__in=include_source_ids)
        else:
            query = query.filter(source_id__in=include_source_ids)
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
