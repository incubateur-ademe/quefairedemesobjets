"""Writing clustering suggestions as SuggestionGroupe/SuggestionUnitaire.

1 SuggestionGroupe per cluster, with the chosen parent as parent_revision_acteur,
and SuggestionUnitaires converted from the changes prepared by
cluster_acteurs_suggestions_prepare:
- parent to create/keep: 1 SuggestionUnitaire per field of its new data
  (ParentRevisionActeur)
- acteur to point to the parent: 1 SuggestionUnitaire parent_id (RevisionActeur)
- acteur already child of the parent: 1 SuggestionUnitaire parent_id with the
  current parent, which changes nothing but can be edited (emptied) to detach
  the acteur from the cluster
- parent to delete: 1 SuggestionUnitaire without field (ParentRevisionActeur)
"""

import json
import logging

import pandas as pd
from cluster.config.constants import COL_PARENT_DATA_NEW, COL_PARENT_ID_BEFORE
from cluster.tasks.business_logic.cluster_acteurs_suggestions.context import (
    suggestion_context_generate,
)
from cluster.tasks.business_logic.misc.df_metadata_get import df_metadata_get
from utils import logging_utils as log

logger = logging.getLogger(__name__)

MODELE_REVISION_ACTEUR = "RevisionActeur"
MODELE_PARENT_REVISION_ACTEUR = "ParentRevisionActeur"

# Grouped fields, the same way as the source suggestions
GROUPED_FIELDS = [("latitude", "longitude")]


def _json_ready(value):
    """Make a dataframe value storable in a JSONField"""
    if isinstance(value, (list, tuple)):
        return [_json_ready(v) for v in value]
    if isinstance(value, dict):
        return {k: _json_ready(v) for k, v in value.items()}
    # numpy scalars
    if hasattr(value, "item"):
        value = value.item()
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _valeur_to_str(value) -> str:
    """SuggestionUnitaire.valeurs are strings"""
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return str(value)


def _unitaires_parent(change: dict) -> list[dict]:
    """1 unitaire per field of the parent data (latitude/longitude grouped), or
    1 unitaire without field if there is no data, so the change exists"""
    data = change["model_params"].get("data") or {}
    champs_groupes = [
        champs for champs in GROUPED_FIELDS if all(champ in data for champ in champs)
    ]
    champs_traites = {champ for champs in champs_groupes for champ in champs}
    champs_groupes += [(champ,) for champ in data if champ not in champs_traites]
    if not champs_groupes:
        champs_groupes = [()]
    return [
        {
            "modele": MODELE_PARENT_REVISION_ACTEUR,
            "identifiant_unique": change["model_params"]["id"],
            "champs": list(champs),
            "valeurs": [_valeur_to_str(data[champ]) for champ in champs],
        }
        for champs in champs_groupes
    ]


def cluster_suggestion_groupe_prepare(
    df_cluster: pd.DataFrame,
    suggestion: dict,
    cluster_fields_exact: list[str],
    cluster_fields_fuzzy: list[str],
) -> dict | None:
    """Prepare 1 groupe (without writing it) for 1 cluster:
    {"contexte": {...}, "metadata": {...}, "fks": {...}, "unitaires": [{modele,
    identifiant_unique, champs, valeurs, ordre, raison, parametres}]}"""
    from data.models.changes import (
        ChangeActeurCreateAsParent,
        ChangeActeurDeleteAsParent,
        ChangeActeurKeepAsParent,
        ChangeActeurUpdateParentId,
        ChangeActeurVerifyRevision,
    )

    # Same context as the legacy suggestions, also validates the exact fields
    contexte = suggestion_context_generate(
        df_cluster=df_cluster,
        cluster_fields_exact=cluster_fields_exact,
        cluster_fields_fuzzy=cluster_fields_fuzzy,
    )
    if contexte is None:
        return None

    changes = sorted(suggestion["changes"], key=lambda c: c["order"])
    change_by_id = {change["model_params"]["id"]: change for change in changes}

    parent_id = None
    unitaires = []
    for change in changes:
        model_name = change["model_name"]
        identifiant_unique = change["model_params"]["id"]
        if model_name in [
            ChangeActeurCreateAsParent.name(),
            ChangeActeurKeepAsParent.name(),
        ]:
            parent_id = identifiant_unique
            change_unitaires = _unitaires_parent(change)
        elif model_name == ChangeActeurUpdateParentId.name():
            change_unitaires = [
                {
                    "modele": MODELE_REVISION_ACTEUR,
                    "identifiant_unique": identifiant_unique,
                    "champs": ["parent_id"],
                    "valeurs": [change["model_params"]["data"]["parent_id"]],
                }
            ]
        elif model_name == ChangeActeurVerifyRevision.name():
            # Already child of the parent: nothing to change, but displayed and
            # editable to detach the acteur
            row = df_cluster[df_cluster["identifiant_unique"] == identifiant_unique]
            current_parent_id = row[COL_PARENT_ID_BEFORE].iloc[0]
            change_unitaires = [
                {
                    "modele": MODELE_REVISION_ACTEUR,
                    "identifiant_unique": identifiant_unique,
                    "champs": ["parent_id"],
                    "valeurs": [_valeur_to_str(current_parent_id)],
                }
            ]
        elif model_name == ChangeActeurDeleteAsParent.name():
            change_unitaires = [
                {
                    "modele": MODELE_PARENT_REVISION_ACTEUR,
                    "identifiant_unique": identifiant_unique,
                    "champs": [],
                    "valeurs": [],
                }
            ]
        else:
            raise ValueError(f"Unexpected model_name: {model_name}")

        for unitaire in change_unitaires:
            unitaire["ordre"] = change["order"]
            unitaire["raison"] = change["reason"]
            unitaire["parametres"] = {"change_model_name": model_name}
        unitaires.extend(change_unitaires)

    if parent_id is None:
        raise ValueError(f"Pas de parent pour {contexte['cluster_id']=}")

    # Unlike the legacy context, all the acteurs of the cluster are listed,
    # including the existing children and the parents to delete
    acteurs = []
    for _, row in df_cluster.iterrows():
        acteur = {
            key: _json_ready(value)
            for key, value in row.to_dict().items()
            if key != COL_PARENT_DATA_NEW
        }
        change = change_by_id.get(acteur["identifiant_unique"])
        if change:
            acteur["change_model_name"] = change["model_name"]
            acteur["change_reason"] = change["reason"]
            acteur["change_order"] = change["order"]
        acteurs.append(acteur)

    contexte = _json_ready(
        {
            **contexte,
            "title": suggestion.get("title"),
            "parent_id": parent_id,
            "cluster_fields_exact": cluster_fields_exact,
            "cluster_fields_fuzzy": cluster_fields_fuzzy,
            "acteurs": acteurs,
        }
    )
    return {
        "contexte": contexte,
        "metadata": _json_ready(df_metadata_get(df_cluster)),
        "fks": {"parent_revision_acteur_id": parent_id},
        "unitaires": unitaires,
    }


def cluster_acteurs_suggestions_to_db_groupes(
    df_clusters: pd.DataFrame,
    suggestions: list[dict],
    identifiant_action: str,
    identifiant_execution: str,
    # For context purposes only
    cluster_fields_exact: list[str],
    cluster_fields_fuzzy: list[str],
) -> None:
    """Writing suggestions to DB as SuggestionGroupe/SuggestionUnitaire"""
    from utils.django import django_setup_full

    django_setup_full()

    logger.info(f"{identifiant_action=}")
    logger.info(f"{identifiant_execution=}")

    from data.models.suggestion import (
        SuggestionAction,
        SuggestionCohorte,
        SuggestionGroupe,
        SuggestionStatut,
        SuggestionUnitaire,
    )
    from django.db import transaction

    cohorte = SuggestionCohorte(
        identifiant_action=identifiant_action,
        identifiant_execution=identifiant_execution,
        type_action=SuggestionAction.CLUSTERING,
        statut=SuggestionStatut.AVALIDER,
        metadata=_json_ready(df_metadata_get(df_clusters)),
    )
    cohorte.save()

    for suggestion in suggestions:
        cluster_id = suggestion["cluster_id"]
        logger.info(f"suggestion {cluster_id=}")
        df_cluster = df_clusters[df_clusters["cluster_id"] == cluster_id]

        if df_cluster.empty:
            msg = "Cluster vide = présent en suggestion mais plus dans df_clusters!!!"
            raise ValueError(msg)

        groupe = cluster_suggestion_groupe_prepare(
            df_cluster=df_cluster,
            suggestion=suggestion,
            cluster_fields_exact=cluster_fields_exact,
            cluster_fields_fuzzy=cluster_fields_fuzzy,
        )
        if groupe is None:
            continue

        log.preview(f"{cluster_id=} unitaires", groupe["unitaires"])
        with transaction.atomic():
            suggestion_groupe = SuggestionGroupe.objects.create(
                suggestion_cohorte=cohorte,
                statut=SuggestionStatut.AVALIDER,
                contexte=groupe["contexte"],
                metadata=groupe["metadata"],
                **groupe["fks"],
            )
            for unitaire in groupe["unitaires"]:
                modele = unitaire["modele"]
                identifiant_unique = unitaire["identifiant_unique"]
                is_revision = modele == MODELE_REVISION_ACTEUR
                SuggestionUnitaire.objects.create(
                    suggestion_groupe=suggestion_groupe,
                    statut=SuggestionStatut.AVALIDER,
                    acteur_id=identifiant_unique if is_revision else None,
                    revision_acteur_id=identifiant_unique if is_revision else None,
                    parent_revision_acteur_id=(
                        None if is_revision else identifiant_unique
                    ),
                    suggestion_modele=modele,
                    ordre=unitaire["ordre"],
                    raison=unitaire["raison"],
                    parametres=unitaire["parametres"],
                    champs=unitaire["champs"],
                    valeurs=unitaire["valeurs"],
                )
