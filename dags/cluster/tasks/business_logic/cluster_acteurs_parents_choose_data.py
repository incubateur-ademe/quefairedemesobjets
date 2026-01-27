import logging
from typing import Any

import pandas as pd
from cluster.config.constants import COL_PARENT_DATA_NEW, FIELDS_PARENT_DATA_EXCLUDED
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def fields_to_include_clean(
    fields_to_include: list[str],
) -> list[str]:
    """To make more explicit and systematically excluded unwanted fields
    (internal, calculated, etc.) from the fields to include."""
    return [x for x in fields_to_include if x not in FIELDS_PARENT_DATA_EXCLUDED]


def value_is_empty(value) -> bool:
    """Consequence of allowing empty strings in DB"""
    return value is None or isinstance(value, str) and value.strip() == ""


def field_pick_value(
    field: str,
    values: list[Any],
    keep_empty: bool = False,
) -> Any:
    """Get the value of a field from a list of acteurs whilst
    ensuring the value is compliant with our models.

    DO NOT sort acteurs here with

    Args:
        acteurs (list[dict]): a sorted list of acteurs to consider
        field (str): field to get
        keep_empty (bool): if True, keep None values in the result if they come

    Returns:
        value: the value of the field
    """
    # TODO: we do want to inherit from the oldest cree_le
    # from cluster acteurs
    for value in values:
        if not value_is_empty(value) or keep_empty:
            try:
                # TODO: once we have fixed the validation mess we should
                # be able to rely on RevisionActeur.full_clean() only
                # TODO: we should also be able to rely on individual field
                # validation and not have to reconstruct an entire acteur
                # (e.g. now it's asking for acteur type etc...)
                """
                data = {field: value}
                Acteur(**data).full_clean()
                RevisionActeur(**data).full_clean()
                """
                return value
            except Exception as e:
                logger.error(f"Invalid value for field {field}: {value}: {e}")
                pass
    return None


def cluster_acteurs_parents_choose_data(
    df_clusters: pd.DataFrame,
    fields_to_include: list[str],
    exclude_source_ids: list[int],
    prioritize_source_ids: list[int],
    keep_empty: bool = False,
    keep_parent_data_by_default: bool = True,
) -> pd.DataFrame:
    from data.models.change import COL_CHANGE_MODEL_NAME
    from data.models.changes import ChangeActeurCreateAsParent, ChangeActeurKeepAsParent
    from qfdmo.models.acteur import VueActeur

    def parent_choose_data(
        parent: VueActeur | None,
        acteurs_list: list[VueActeur],
        fields_to_include: list[str],
        prioritize_source_ids: list[int],
        keep_empty: bool = False,
        keep_parent_data_by_default: bool = True,
    ) -> dict:
        """Selects and assigns data for a parent. Since the data is
        intended to create or enrich a revision, we ensure that the chosen data
        satisfies the RevisionActor model.

        Args:
            acteurs (list[dict]): list of acteurs to consider = Priority 1
            fields_to_include (list[str]): fields to include in the result = Fallback
            exclusion_always_sources (list[str]): sources to exclude for all fields
            priority_always_sources (list[str]): sources to prioritize for all fields
            keep_empty (bool): if True, keep None values in the result if they come
                from priority sources
        """

        # Priority = as per priority list OR rest by default
        def source_priority(a):
            return (
                prioritize_source_ids.index(a.source.id)
                if a.source and a.source.id in prioritize_source_ids
                else float("inf")
            )

        acteurs_list = sorted(acteurs_list, key=source_priority)

        # On parent creation, we don't want to keep empty data
        if not parent:
            keep_empty = False
        if parent and keep_parent_data_by_default:
            acteurs_list = [parent] + acteurs_list

        # Fields: make sure we don't include unwanted fields
        fields = fields_to_include_clean(fields_to_include)  # TODO : check which

        result = {}
        for field in fields:
            value_old = getattr(parent, field) if parent else None
            values = [getattr(a, field) for a in acteurs_list]
            value_new = field_pick_value(
                field,
                values,
                keep_empty,
            )
            if value_new == value_old:
                continue
            if value_new is None and not keep_empty:
                continue
            result[field] = value_new

        return result

    """For all selected parents in clusters, select the data to use"""
    fields = fields_to_include_clean(fields_to_include)
    fields += ["source_id"]

    df_clusters[COL_PARENT_DATA_NEW] = None
    for _, df_cluster in df_clusters.groupby("cluster_id"):
        filter_parent = df_cluster[COL_CHANGE_MODEL_NAME].isin(
            [
                ChangeActeurCreateAsParent.name(),
                ChangeActeurKeepAsParent.name(),
            ]
        )
        df_parents = df_cluster[filter_parent]
        # TODO: too much validation scattered: refactor pipeline with
        # Pydantic models (eg ClusterModel) which have necessary validation
        # and methods (and methods can call validation each time so we
        # identify breaking points easily/automatically)
        assert len(df_parents) == 1, "Should have 1 parent per cluster"
        parent_iloc = df_parents.index[0]
        parent_id = df_parents["identifiant_unique"].iloc[0]

        df_acteurs = df_cluster[~filter_parent]
        acteur_ids = df_acteurs["identifiant_unique"].unique()

        # We only need to get the parent's before data IF
        # it was an existing one (i.e. one to keep)
        parent = None
        if (
            df_parents[COL_CHANGE_MODEL_NAME].values[0]
            == ChangeActeurKeepAsParent.name()
        ):
            try:
                parent = VueActeur.objects.get(pk=parent_id)
            except VueActeur.DoesNotExist:
                ptype = df_parents[COL_CHANGE_MODEL_NAME].values[0]
                raise ValueError(f"Parent {ptype} {parent_id} pas dans revision!!!")

        # We construct a list of acteurs, 1st from revision (higher prio
        # as might contain business-approved changes) and then from base
        acteurs = VueActeur.objects.filter(pk__in=acteur_ids).exclude(
            source__id__in=exclude_source_ids
        )
        parent_data_new = parent_choose_data(
            parent=parent,
            acteurs_list=list(acteurs),
            fields_to_include=fields,
            prioritize_source_ids=prioritize_source_ids,
            keep_empty=keep_empty,
            keep_parent_data_by_default=keep_parent_data_by_default,
        )

        df_clusters.at[parent_iloc, COL_PARENT_DATA_NEW] = parent_data_new

    return df_clusters
