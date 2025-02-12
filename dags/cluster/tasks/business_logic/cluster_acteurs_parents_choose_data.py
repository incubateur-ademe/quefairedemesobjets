import pandas as pd
from cluster.config.model import FIELDS_PROTECTED_ALL
from django.forms.models import model_to_dict
from utils.django import django_setup_full

django_setup_full()
from data.models.change import (  # noqa: E402
    CHANGE_ACTEUR_CREATE_AS_PARENT,
    CHANGE_ACTEUR_PARENT_KEEP,
    COL_CHANGE_DATA,
    COL_CHANGE_TYPE,
)
from qfdmo.models.acteur import (  # noqa: E402
    BaseActeur,
    DisplayedActeur,
    RevisionActeur,
)


def fields_to_include_clean(
    fields_to_include: list[str],
) -> list[str]:
    """To make more explicit and systematically excluded unwanted fields
    (internal, calculated, etc.) from the fields to include."""
    return [x for x in fields_to_include if x not in FIELDS_PROTECTED_ALL]


def value_is_empty(value) -> bool:
    """Consequence of allowing empty strings in DB"""
    return value is None or isinstance(value, str) and value.strip() == ""


def acteurs_field_value_get_one(
    acteurs: list[dict],
    field: str,
    prioritize_source_ids: list[int],
    consider_empty: bool = False,
):
    """Get the values of a field from a list of acteurs"""
    for acteur in acteurs:
        value = acteur.get(field)
        if not value_is_empty(value) or (
            acteur["source_id"] in prioritize_source_ids and consider_empty
        ):
            return value
    return None


def cluster_acteurs_one_parent_choose_data(
    parent_data_before: dict,
    acteurs_revision: list[dict],
    acteurs_base: list[dict],
    fields_to_include: list[str],
    exclude_source_ids: list[int],
    prioritize_source_ids: list[int],
    consider_empty: bool = False,
) -> dict:
    """Selects and assigns data for a parent. Since the data is
    intended to create or enrich a revision, we ensure that the chosen data
    satisfies the RevisionActor model.

    Args:
        acteurs (list[dict]): list of acteurs to consider = Priority 1
        fields_to_include (list[str]): fields to include in the result = Fallback
        exclusion_always_sources (list[str]): sources to exclude for all fields
        priority_always_sources (list[str]): sources to prioritize for all fields
        consider_empty (bool): if True, keep None values in the result if they come
            from priority sources
    """

    # Priority = as per priority list OR rest by default
    def source_priority(a):
        return (
            prioritize_source_ids.index(a["source_id"])
            if a["source_id"] in prioritize_source_ids
            else float("inf")
        )

    # Acteurs to consider: first revisions, then base, but not from excluded sources
    acteurs = []
    acteurs += [a for a in acteurs_revision if a["source_id"] not in exclude_source_ids]
    acteurs.sort(key=source_priority)
    acteurs += [a for a in acteurs_base if a["source_id"] not in exclude_source_ids]
    acteurs.sort(key=source_priority)

    # Fields: make sure we don't include unwanted fields
    fields = fields_to_include_clean(fields_to_include)

    result = {}
    for field in fields:
        value_old = parent_data_before.get(field)
        value_new = acteurs_field_value_get_one(
            acteurs=acteurs,
            field=field,
            prioritize_source_ids=prioritize_source_ids,
            consider_empty=consider_empty,
        )
        if value_new is not None and value_new != value_old:
            result[field] = value_new

    return result


def cluster_acteurs_parents_choose_data(
    df_clusters: pd.DataFrame,
    fields_to_include: list[str],
    exclude_source_ids: list[int],
    prioritize_source_ids: list[int],
    consider_empty: bool = False,
) -> pd.DataFrame:
    """For all selected parents in clusters, select the data to use"""
    fields = fields_to_include_clean(fields_to_include)

    df_clusters[COL_CHANGE_DATA] = None
    for cluster_id in df_clusters.groupby("cluster_id"):
        df_cluster = df_clusters[df_clusters["cluster_id"] == cluster_id]
        filter_parent = df_cluster[COL_CHANGE_TYPE].isin(
            [
                CHANGE_ACTEUR_CREATE_AS_PARENT,
                CHANGE_ACTEUR_PARENT_KEEP,
            ]
        )
        df_acteurs = df_cluster[~filter_parent]
        df_parents = df_cluster[filter_parent]
        # TODO: remove below once we have added validation functions and e2e tests
        # which should cover this case
        assert len(df_parents) == 1, "Should have 1 parent per cluster"
        parent_iloc = df_parents.index[0]
        parent_id = df_parents["identifiant_unique"].iloc[0]
        acteur_ids = df_acteurs["identifiant_unique"].unique()

        # We construct a list of acteurs, 1st from revision (higher prio
        # as might contain business-approved changes) and then from base
        parent = DisplayedActeur.objects.get(pk=parent_id)
        parent_data_before = model_to_dict(parent)
        acteurs_revision = RevisionActeur.objects.filter(pk__in=acteur_ids).values(
            *fields
        )
        acteurs_base = BaseActeur.objects.filter(pk__in=acteur_ids).values(*fields)

        parent_data_after = {
            "identifiant_unique": parent_id,
            "data": cluster_acteurs_one_parent_choose_data(
                parent_data_before=parent_data_before,
                acteurs_revision=list(acteurs_revision),
                acteurs_base=list(acteurs_base),
                fields_to_include=fields,
                exclude_source_ids=exclude_source_ids,
                prioritize_source_ids=prioritize_source_ids,
                consider_empty=consider_empty,
            ),
        }
        df_clusters.iloc[parent_iloc, COL_CHANGE_DATA] = parent_data_after

    return df_clusters
