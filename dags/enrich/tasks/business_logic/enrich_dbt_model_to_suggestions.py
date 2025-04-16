import logging
from datetime import datetime, timezone

import pandas as pd
from cluster.tasks.business_logic.cluster_acteurs_parents_choose_new import (
    parent_id_generate,
)
from enrich.config import COHORTS, COLS, Cohort
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def suggestion_change_prepare(
    model,
    model_params: dict,
    order: int,
    reason: str,
    entity_type: str,
) -> dict:
    """Generic utility to prepare, validate and
    serialize 1 suggestion change for all suggestion types"""
    from data.models.change import SuggestionChange

    model(**model_params).validate()
    return SuggestionChange(
        order=order,
        reason=reason,
        entity_type=entity_type,
        model_name=model.name(),
        model_params=model_params,
    ).model_dump()


def suggestion_change_prepare_closed_not_replaced(
    row: dict,
) -> list[dict]:
    """Prepare suggestions for closed not replaced cohorts"""
    from data.models.changes import ChangeActeurUpdateData
    from qfdmo.models import ActeurStatus

    changes = []
    model_params = {
        "id": row[COLS.ACTEUR_ID],
        "data": {
            "identifiant_unique": row[COLS.ACTEUR_ID],
            "statut": ActeurStatus.INACTIF,
            # TODO: fix inconsistency between acteur_siret and siret
            # in non-replaced model
            "siret": row[COLS.ACTEUR_SIRET],
            "siret_is_closed": True,
            "acteur_type": row[COLS.ACTEUR_TYPE_ID],
            "source": row[COLS.ACTEUR_SOURCE_ID],
        },
    }
    changes.append(
        suggestion_change_prepare(
            model=ChangeActeurUpdateData,
            model_params=model_params,
            order=1,
            reason="SIRET & SIREN fermés, 0 remplacement trouvé",
            entity_type="acteur_displayed",
        )
    )
    return changes


def suggestion_change_prepare_closed_replaced(
    row: dict,
) -> list[dict]:
    """Prepare suggestions for closed replaced cohorts"""
    from data.models.changes import (
        ChangeActeurCreateAsChild,
        ChangeActeurCreateAsParent,
        ChangeActeurUpdateData,
    )
    from qfdmo.models import ActeurStatus

    changes = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Parent
    parent_id = parent_id_generate([str(row[COLS.REMPLACER_SIRET])])
    params_parent = {
        "id": parent_id,
        "data": {
            "identifiant_unique": parent_id,
            "nom": row[COLS.REMPLACER_NOM],
            "adresse": row[COLS.REMPLACER_ADRESSE],
            "code_postal": row[COLS.REMPLACER_CODE_POSTAL],
            "ville": row[COLS.REMPLACER_VILLE],
            "siren": row[COLS.REMPLACER_SIRET][:9],
            "siret": row[COLS.REMPLACER_SIRET],
            "naf_principal": row[COLS.REMPLACER_NAF],
            "acteur_type": row[COLS.ACTEUR_TYPE_ID],
            "source": None,
            "statut": ActeurStatus.ACTIF,
        },
    }
    changes.append(
        suggestion_change_prepare(
            model=ChangeActeurCreateAsParent,
            model_params=params_parent,
            order=1,
            reason="besoin d'un parent pour rattaché acteur fermé",
            entity_type="acteur_displayed",
        )
    )

    # New child to hold the reference data as standalone
    # as parents are surrogates (e.g. they can be deleted
    # during clustering)
    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    child_new_id = f"{row[COLS.ACTEUR_ID]}_{row[COLS.ACTEUR_SIRET]}_{now}"
    params_child_new = params_parent.copy()
    params_child_new["id"] = child_new_id
    params_child_new["data"]["identifiant_unique"] = child_new_id
    params_child_new["data"]["source"] = row[COLS.ACTEUR_SOURCE_ID]
    params_child_new["data"]["parent"] = parent_id
    params_child_new["data"]["parent_reason"] = (
        f"Nouvel enfant pour conserver les données suite à: "
        f"SIRET {row[COLS.ACTEUR_SIRET]} "
        f"détecté le {today} comme fermé dans AE, "
        f"remplacé par SIRET {row[COLS.REMPLACER_SIRET]}"
    )
    if row[COLS.ACTEUR_LONGITUDE] is not None and row[COLS.ACTEUR_LATITUDE] is not None:
        params_child_new["data"]["longitude"] = row[COLS.ACTEUR_LONGITUDE]
        params_child_new["data"]["latitude"] = row[COLS.ACTEUR_LATITUDE]
    changes.append(
        suggestion_change_prepare(
            model=ChangeActeurCreateAsChild,
            model_params=params_child_new,
            order=2,
            reason="besoin nouvel enfant pour conserver les données",
            entity_type="acteur_displayed",
        )
    )

    # Existing Child
    params_child_old = params_child_new.copy()
    params_child_old["id"] = row[COLS.ACTEUR_ID]
    params_child_old["data"]["identifiant_unique"] = row[COLS.ACTEUR_ID]
    params_child_old["data"]["parent"] = parent_id
    params_child_old["data"]["parent_reason"] = (
        f"SIRET {row[COLS.ACTEUR_SIRET]} "
        f"détecté le {today} comme fermé dans AE, "
        f"remplacé par SIRET {row[COLS.REMPLACER_SIRET]}"
    )
    params_child_old["data"]["siret_is_closed"] = True
    params_child_old["data"]["statut"] = ActeurStatus.INACTIF
    changes.append(
        suggestion_change_prepare(
            model=ChangeActeurUpdateData,
            model_params=params_child_old,
            order=3,
            reason="rattacher enfant fermé à un parent",
            entity_type="acteur_displayed",
        )
    )
    return changes


def enrich_dbt_model_to_suggestions(
    df: pd.DataFrame,
    cohort: Cohort,
    identifiant_action: str,
    dry_run: bool = True,
) -> bool:
    from data.models.suggestion import (
        Suggestion,
        SuggestionAction,
        SuggestionCohorte,
        SuggestionStatut,
    )

    # Validation
    if df is None or df.empty:
        raise ValueError("df vide: on devrait pas être ici")

    cohort_codes = list(df[COLS.SUGGEST_COHORT_CODE].unique())
    if len(cohort_codes) != 1 or cohort_codes[0] != cohort.code:
        msg = f"Problème cohorte: obtenu {cohort_codes=} vs. attendu {cohort.code=}"
        raise ValueError(msg)

    # Suggestions
    suggestions = []
    for _, row in df.iterrows():
        row = dict(row)

        try:
            # -----------------------------------------
            # NOT REPLACED
            # -----------------------------------------
            if cohort == COHORTS.CLOSED_NOT_REPLACED:
                changes = suggestion_change_prepare_closed_not_replaced(row)

            # -----------------------------------------
            # REPLACED
            # -----------------------------------------
            elif cohort in [
                COHORTS.CLOSED_REP_OTHER_SIREN,
                COHORTS.CLOSED_REP_SAME_SIREN,
            ]:
                changes = suggestion_change_prepare_closed_replaced(row)

        except Exception as e:
            log.preview("🔴 Suggestion problématique", row)
            logger.error(f"Erreur de préparation des changements: {e}")
            continue

        # Creating a suggestion with the given changes
        suggestions.append(
            {
                "contexte": {},
                "suggestion": {
                    "title": cohort.label,
                    "summary": [],
                    "changes": changes,
                },
            }
        )

    if not suggestions:
        raise ValueError("Aucune suggestion à écrire, pas normal")

    # -----------------------------------------
    # DRY RUN: STOP HERE
    # -----------------------------------------
    if dry_run:
        logger.info("✋ Dry run: suggestions pas écrites en base")
        suggestions_written = False
        return suggestions_written

    # -----------------------------------------
    # SUGGESTION: WRITE TO DB
    # -----------------------------------------
    db_cohort = SuggestionCohorte(
        identifiant_action=identifiant_action,
        identifiant_execution=f"{cohort.label}",
        statut=SuggestionStatut.AVALIDER,
        type_action=SuggestionAction.ENRICH_ACTEURS_CLOSED,
        metadata={"🔢 Nombre de suggestions": len(suggestions)},
    )
    db_cohort.save()
    for suggestion in suggestions:
        Suggestion(
            suggestion_cohorte=db_cohort,
            statut=SuggestionStatut.AVALIDER,
            contexte=suggestion["contexte"],
            suggestion=suggestion["suggestion"],
        ).save()
    suggestions_written = True
    return suggestions_written
