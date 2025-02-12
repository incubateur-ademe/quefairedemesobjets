import pandas as pd
from cluster.config.model import FIELDS_PROTECTED_ALL
from cluster.tasks.business_logic.cluster_acteurs_parents_choose_new import (
    clusters_to_children_and_orphans_get,
    clusters_to_parents_get,
)
from rich import print
from utils.django import django_setup_full

django_setup_full()
from qfdmo.models.acteur import BaseActeur, RevisionActeur  # noqa: E402


def fields_to_include_clean(
    fields_to_include: list[str],
) -> list[str]:
    """To make more explicit and systematically excluded unwanted fields
    (internal, calculated, etc.) from the fields to include."""
    return [x for x in fields_to_include if x not in FIELDS_PROTECTED_ALL]


def acteurs_field_result_assign(
    result_try: dict,
    result_final: dict,
    acteurs: list[dict],
    field: str,
    priority_always_source_ids: list[int],
    keep_none: bool = False,
):
    """Get the values of a field from a list of acteurs"""
    for acteur in acteurs:
        value = acteur.get(field)
        if value is not None or (
            value is None
            and acteur["source_id"] in priority_always_source_ids
            and keep_none
        ):
            # Where we try to make it work
            # and only keep what works
            result_try[field] = value
            try:
                print(f"\n\n{field=}")
                print(f"{str(value)=}")
                rev = RevisionActeur(**result_try)
                rev.full_clean()
                # act = Acteur(**result_try)
                # act.full_clean()
                print(f"{str(getattr(rev, field))=}")
                # We take the rev version as it might have
                # changed after full_clean
                result_final[field] = getattr(rev, field)
                break
            except Exception as e:
                print(f"Error: {e}")
                pass


def cluster_acteurs_one_parent_choose_data(
    acteurs_revision: list[dict],
    acteurs_base: list[dict],
    fields_to_include: list[str],
    exclusion_always_source_ids: list[int],
    priority_always_source_ids: list[int],
    keep_none: bool = False,
) -> dict:
    """Selects and assigns data for a parent. Since the data is
    intended to create or enrich a revision, we ensure that the chosen data
    satisfies the RevisionActor model.

    Args:
        acteurs (list[dict]): list of acteurs to consider
        fields_to_include (list[str]): fields to include in the result
        exclusion_always_sources (list[str]): sources to exclude for all fields
        priority_always_sources (list[str]): sources to prioritize for all fields
        keep_none (bool): if True, keep None values in the result if they come
            from priority sources
    """
    # One for trying on RevisionActeur
    # and the other with what's working
    result_try = {}
    result_final = {}

    # Acteurs to consider
    rev_valid = [
        a for a in acteurs_revision if a["source_id"] not in exclusion_always_source_ids
    ]
    base_valid = [
        a for a in acteurs_base if a["source_id"] not in exclusion_always_source_ids
    ]

    # Priority = as per priority list OR rest by default
    def source_priority(a):
        return (
            priority_always_source_ids.index(a["source_id"])
            if a["source_id"] in priority_always_source_ids
            else float("inf")
        )

    rev_valid.sort(key=source_priority)
    base_valid.sort(key=source_priority)

    # Fields: make sure we don't include unwanted fields
    fields = fields_to_include_clean(fields_to_include)

    for field in fields:
        acteurs_field_result_assign(
            result_try=result_try,
            result_final=result_final,
            acteurs=rev_valid,
            field=field,
            priority_always_source_ids=priority_always_source_ids,
            keep_none=keep_none,
        )
        acteurs_field_result_assign(
            result_try=result_try,
            result_final=result_final,
            acteurs=base_valid,
            field=field,
            priority_always_source_ids=priority_always_source_ids,
            keep_none=keep_none,
        )

    return result_final


def cluster_acteurs_parents_choose_data(
    df_clusters: pd.DataFrame,
    fields_to_include: list[str],
    exclusion_always_source_ids: list[int],
    priority_always_source_ids: list[int],
    keep_none: bool = False,
) -> dict:
    """For all selected parents in clusters, select the data to use"""
    results = {}

    fields = fields_to_include_clean(fields_to_include)

    # Cluster ID -> Parent ID
    # Cluster ID -> Children and Orphans IDs
    c_ids_to_parent_id = clusters_to_parents_get(df_clusters)
    c_ids_to_children_and_orphans_ids = clusters_to_children_and_orphans_get(
        df_clusters
    )

    for cluster_id, parent_id in c_ids_to_parent_id.items():
        acteur_ids = c_ids_to_children_and_orphans_ids[cluster_id]

        # We construct a list of acteurs, 1st from revision (higher prio
        # as might contain business-approved changes) and then from base
        acteurs_revision = RevisionActeur.objects.filter(
            identifiant_unique__in=acteur_ids
        ).values(*fields)
        acteurs_base = BaseActeur.objects.filter(
            identifiant_unique__in=acteur_ids
        ).values(*fields)

        results[cluster_id] = {
            "identifiant_unique": parent_id,
            "data": cluster_acteurs_one_parent_choose_data(
                acteurs_revision=list(acteurs_revision),
                acteurs_base=list(acteurs_base),
                fields_to_include=fields,
                exclusion_always_source_ids=exclusion_always_source_ids,
                priority_always_source_ids=priority_always_source_ids,
                keep_none=keep_none,
            ),
        }

    return results
