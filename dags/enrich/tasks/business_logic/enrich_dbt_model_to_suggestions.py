import logging
from datetime import datetime, timezone

import pandas as pd
from cluster.tasks.business_logic.cluster_acteurs_parents_choose_new import (
    parent_id_generate,
)
from enrich.config.cohorts import COHORTS
from enrich.config.columns import COLS
from enrich.tasks.business_logic.enrich_dbt_model_row_to_suggest_data import (
    dbt_model_row_to_suggest_data,
)
from utils import logging_utils as log

from data.models.changes.acteur_rgpd_anonymize import rgpd_data_get

logger = logging.getLogger(__name__)


def changes_prepare(
    model,
    model_params: dict,
    order: int,
    reason: str,
    entity_type: str,
) -> dict:
    """Generic utility to prepare, validate and
    serialize 1 suggestion change for ANY suggestion types"""
    from data.models.change import SuggestionChange

    model(**model_params).validate()
    return SuggestionChange(
        order=order,
        reason=reason,
        entity_type=entity_type,
        model_name=model.name(),
        model_params=model_params,
    ).model_dump()


def changes_prepare_villes(row: dict) -> tuple[list[dict], dict]:
    """Prepare suggestions for villes cohorts"""
    from data.models.changes import ChangeActeurUpdateData

    changes = []
    model_params = {
        "id": row[COLS.ACTEUR_ID],
        "data": {
            "ville": row[COLS.SUGGEST_VILLE],
        },
    }
    changes.append(
        changes_prepare(
            model=ChangeActeurUpdateData,
            model_params=model_params,
            order=1,
            reason="On fait confiance à la BAN",
            entity_type="acteur_displayed",
        )
    )
    contexte = {
        "statut": row[COLS.ACTEUR_STATUT],
        "adresse": row[COLS.ACTEUR_ADRESSE],
        "ville": row[COLS.ACTEUR_VILLE],
        "code_postal": row[COLS.ACTEUR_CODE_POSTAL],
    }
    return changes, contexte


def changes_prepare_rgpd(
    row: dict,
) -> tuple[list[dict], dict]:
    """Prepare suggestions for RGPD cohorts"""
    from data.models.changes import ChangeActeurRgpdAnonymize

    changes = []
    model_params = {
        "id": row[COLS.ACTEUR_ID],
        "data": rgpd_data_get(),
    }
    changes.append(
        changes_prepare(
            model=ChangeActeurRgpdAnonymize,
            model_params=model_params,
            order=1,
            reason="🕵 Anonymisation RGPD",
            entity_type="acteur_displayed",
        )
    )
    contexte = {
        "statut": row[COLS.ACTEUR_STATUT],
        "noms d'origine": row[COLS.ACTEUR_NOMS_ORIGINE],
    }
    return changes, contexte


def changes_prepare_closed_not_replaced(
    row: dict,
) -> tuple[list[dict], dict]:
    """Prepare suggestions for closed not replaced cohorts"""
    from data.models.changes import ChangeActeurUpdateData
    from qfdmo.models import ActeurStatus

    changes = []
    model_params = {
        "id": row[COLS.ACTEUR_ID],
        "data": {
            "statut": ActeurStatus.INACTIF,
            "siret": row[COLS.ACTEUR_SIRET],
            "siren": row[COLS.ACTEUR_SIRET][:9],
            "siret_is_closed": True,
            "acteur_type": row[COLS.ACTEUR_TYPE_ID],
            "source": row[COLS.ACTEUR_SOURCE_ID],
        },
    }
    changes.append(
        changes_prepare(
            model=ChangeActeurUpdateData,
            model_params=model_params,
            order=1,
            reason="SIRET & SIREN fermés, 0 remplacement trouvé",
            entity_type="acteur_displayed",
        )
    )
    contexte = {}  # changes are self-explanatory
    return changes, contexte


def changes_prepare_closed_replaced(
    row: dict,
) -> tuple[list[dict], dict]:
    """Prepare suggestion changes for closed replaced cohorts"""
    from data.models.changes import (
        ChangeActeurCreateAsChild,
        ChangeActeurCreateAsParent,
        ChangeActeurUpdateData,
    )
    from qfdmo.models import ActeurStatus

    changes = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Parent
    parent_id = parent_id_generate([str(row[COLS.SUGGEST_SIRET])])
    parent_data = dbt_model_row_to_suggest_data(row)
    parent_data["source"] = None
    parent_data["statut"] = ActeurStatus.ACTIF
    params_parent = {
        "id": parent_id,
        "data": parent_data,
    }
    changes.append(
        changes_prepare(
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
    params_child_new["data"]["source"] = row[COLS.ACTEUR_SOURCE_ID]
    params_child_new["data"]["parent"] = parent_id
    params_child_new["data"]["parent_reason"] = (
        f"Nouvel enfant pour conserver les données suite à: "
        f"SIRET {row[COLS.ACTEUR_SIRET]} "
        f"détecté le {today} comme fermé dans AE, "
        f"remplacé par SIRET {row[COLS.SUGGEST_SIRET]}"
    )
    changes.append(
        changes_prepare(
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
    params_child_old["data"]["parent"] = parent_id
    params_child_old["data"]["parent_reason"] = (
        f"SIRET {row[COLS.ACTEUR_SIRET]} "
        f"détecté le {today} comme fermé dans AE, "
        f"remplacé par SIRET {row[COLS.SUGGEST_SIRET]}"
    )
    params_child_old["data"]["siret_is_closed"] = True
    params_child_old["data"]["statut"] = ActeurStatus.INACTIF
    changes.append(
        changes_prepare(
            model=ChangeActeurUpdateData,
            model_params=params_child_old,
            order=3,
            reason="rattacher enfant fermé à un parent",
            entity_type="acteur_displayed",
        )
    )
    contexte = {}  # changes are self-explanatory
    return changes, contexte


# Mapping cohorts with their respective changes preparation function
COHORTS_TO_PREPARE_CHANGES = {
    COHORTS.CLOSED_NOT_REPLACED: changes_prepare_closed_not_replaced,
    COHORTS.CLOSED_REP_OTHER_SIREN: changes_prepare_closed_replaced,
    COHORTS.CLOSED_REP_SAME_SIREN: changes_prepare_closed_replaced,
    COHORTS.RGPD: changes_prepare_rgpd,
    COHORTS.VILLES_TYPO: changes_prepare_villes,
    COHORTS.VILLES_NEW: changes_prepare_villes,
}


def enrich_dbt_model_to_suggestions(
    df: pd.DataFrame,
    cohort: str,
    identifiant_action: str,
    dry_run: bool = True,
) -> bool:
    from data.models.suggestion import (
        Suggestion,
        SuggestionAction,
        SuggestionCohorte,
        SuggestionStatut,
    )

    # TODO: once all suggestions have been migrated to pydantic, we no
    # longer need SuggestionCohorte.type_action and any of the following
    # identifiant_execution = cohort AND pydantic models take care of
    # handling the specifics
    COHORTS_TO_SUGGESTION_ACTION = {
        COHORTS.CLOSED_NOT_REPLACED: SuggestionAction.ENRICH_ACTEURS_CLOSED,
        COHORTS.CLOSED_REP_OTHER_SIREN: SuggestionAction.ENRICH_ACTEURS_CLOSED,
        COHORTS.CLOSED_REP_SAME_SIREN: SuggestionAction.ENRICH_ACTEURS_CLOSED,
        COHORTS.RGPD: SuggestionAction.ENRICH_ACTEURS_RGPD,
        COHORTS.VILLES_TYPO: SuggestionAction.ENRICH_ACTEURS_VILLES_TYPO,
        COHORTS.VILLES_NEW: SuggestionAction.ENRICH_ACTEURS_VILLES_NEW,
    }

    # Validation
    if df is None or df.empty:
        raise ValueError("df vide: on devrait pas être ici")

    cohorts = list(df[COLS.SUGGEST_COHORT].unique())
    if len(cohorts) != 1 or cohorts[0] != cohort:
        msg = f"Problème cohorte: obtenu {cohorts=} vs. attendu {cohort=}"
        raise ValueError(msg)

    # Creating suggestion
    suggestions = []
    for _, row in df.iterrows():
        row = dict(row)

        try:
            changes, contexte = COHORTS_TO_PREPARE_CHANGES[cohort](row)
            suggestion = {
                "contexte": contexte,
                "suggestion": {"title": cohort, "changes": changes},
            }
            log.preview("🔢 Suggestion", suggestion)
            suggestions.append(suggestion)

        # We tolerate some errors
        except Exception as e:
            log.preview("🔴 Suggestion problématique", row)
            logger.error(f"Erreur de préparation des changements: {e}")
            continue

    # we need some working suggestions, can't have it all fail
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
        identifiant_execution=f"{cohort}",
        statut=SuggestionStatut.AVALIDER,
        type_action=COHORTS_TO_SUGGESTION_ACTION[cohort],
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
