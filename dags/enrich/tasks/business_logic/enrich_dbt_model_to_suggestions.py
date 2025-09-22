import logging
from datetime import datetime, timezone

import pandas as pd
from enrich.config.cohorts import COHORTS
from enrich.config.columns import COLS
from utils import logging_utils as log

logger = logging.getLogger(__name__)


def changes_prepare(
    model,
    model_params: dict,
    order: int,
    reason: str,
) -> dict:
    """Generic utility to prepare, validate and
    serialize 1 suggestion change for ANY suggestion types"""
    from data.models.change import SuggestionChange

    model(**model_params).validate()
    return SuggestionChange(
        order=order,
        reason=reason,
        model_name=model.name(),
        model_params=model_params,
    ).model_dump()


def changes_prepare_villes(row: dict) -> tuple[list[dict], dict]:
    """Prepare suggestions for villes cohorts"""
    from data.models.changes import ChangeActeurUpdateRevision

    changes = []
    model_params = {
        "id": row[COLS.ACTEUR_ID],
        "data": {
            "ville": row[COLS.SUGGEST_VILLE],
        },
    }
    changes.append(
        changes_prepare(
            model=ChangeActeurUpdateRevision,
            model_params=model_params,
            order=1,
            reason="On fait confiance à la BAN",
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
    from data.models.changes.acteur_rgpd_anonymize import rgpd_data_get

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
        )
    )
    contexte = {
        "noms d'origine": row[COLS.ACTEUR_NOMS_ORIGINE],
        "statut": row[COLS.ACTEUR_STATUT],
    }
    return changes, contexte


def _get_closed_row_contexte(row: dict) -> dict:
    return {
        "nom": row[COLS.ACTEUR_NOM],
        "statut": row[COLS.ACTEUR_STATUT],
        "adresse": row[COLS.ACTEUR_ADRESSE],
        "code_postal": row[COLS.ACTEUR_CODE_POSTAL],
        "ville": row[COLS.ACTEUR_VILLE],
    }


def changes_prepare_closed_not_replaced(
    row: dict,
) -> tuple[list[dict], dict]:
    """Prepare suggestions for closed not replaced cohorts"""
    from data.models.changes import ChangeActeurUpdateRevision
    from qfdmo.models import ActeurStatus

    changes = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    model_params = {
        "id": row[COLS.ACTEUR_ID],
        "data": {
            "statut": ActeurStatus.INACTIF,
            "siret_is_closed": True,
            "parent_reason": (
                f"Modifications de l'acteur le {today}: "
                f"SIRET {row[COLS.ACTEUR_SIRET]} détecté comme fermé dans AE,"
                " Pas de remplacement"
            ),
        },
    }
    changes.append(
        changes_prepare(
            model=ChangeActeurUpdateRevision,
            model_params=model_params,
            order=1,
            reason="SIRET & SIREN fermés, 0 remplacement trouvé",
        )
    )
    contexte = _get_closed_row_contexte(row)
    return changes, contexte


def changes_prepare_closed_replaced(
    row: dict,
) -> tuple[list[dict], dict]:
    """Prepare suggestion changes for closed replaced cohorts"""
    from data.models.changes import ChangeActeurUpdateRevision

    changes = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    update_revision = {
        "id": row[COLS.ACTEUR_ID],
        "data": {
            "siret": row[COLS.SUGGEST_SIRET],
            "siren": row[COLS.SUGGEST_SIRET][:9],
            "siret_is_closed": False,
            "parent_reason": (
                f"Modifications de l'acteur le {today}: "
                f"SIRET {row[COLS.ACTEUR_SIRET]} détecté comme fermé dans AE, "
                f"remplacé par le SIRET {row[COLS.SUGGEST_SIRET]}"
            ),
        },
    }
    changes = [
        changes_prepare(
            model=ChangeActeurUpdateRevision,
            model_params=update_revision,
            order=1,
            reason="Modification du SIRET",
        )
    ]

    contexte = _get_closed_row_contexte(row)
    return changes, contexte


def _changes_prepare_cp(row: dict, model) -> tuple[list[dict], dict]:
    """Prepare suggestions for villes cohorts"""

    changes = []
    model_params = {
        "id": row[COLS.ACTEUR_ID],
        "data": {
            "code_postal": row[COLS.SUGGEST_CODE_POSTAL],
        },
    }
    changes.append(
        changes_prepare(
            model=model,
            model_params=model_params,
            order=1,
            reason="Code postal normalisé",
        )
    )
    context = {
        "code_postal": row["code_postal"],
    }

    return changes, context


def changes_prepare_acteur_cp(row: dict) -> tuple[list[dict], dict]:
    """Prepare suggestions for villes cohorts"""
    from data.models.changes import ChangeActeurUpdate

    return _changes_prepare_cp(row, ChangeActeurUpdate)


def changes_prepare_revision_acteur_cp(row: dict) -> tuple[list[dict], dict]:
    """Prepare suggestions for villes cohorts"""
    from data.models.changes import ChangeActeurUpdateRevision

    return _changes_prepare_cp(row, ChangeActeurUpdateRevision)


# Mapping cohorts with their respective changes preparation function
COHORTS_TO_PREPARE_CHANGES = {
    COHORTS.CLOSED_NOT_REPLACED_UNITE: changes_prepare_closed_not_replaced,
    COHORTS.CLOSED_NOT_REPLACED_ETABLISSEMENT: changes_prepare_closed_not_replaced,
    COHORTS.CLOSED_REP_OTHER_SIREN: changes_prepare_closed_replaced,
    COHORTS.CLOSED_REP_SAME_SIREN: changes_prepare_closed_replaced,
    COHORTS.RGPD: changes_prepare_rgpd,
    COHORTS.VILLES_TYPO: changes_prepare_villes,
    COHORTS.VILLES_NEW: changes_prepare_villes,
    COHORTS.ACTEUR_CP_TYPO: changes_prepare_acteur_cp,
    COHORTS.REVISION_ACTEUR_CP_TYPO: changes_prepare_revision_acteur_cp,
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
        COHORTS.CLOSED_NOT_REPLACED_UNITE: SuggestionAction.ENRICH_ACTEURS_CLOSED,
        COHORTS.CLOSED_NOT_REPLACED_ETABLISSEMENT: (
            SuggestionAction.ENRICH_ACTEURS_CLOSED
        ),
        COHORTS.CLOSED_REP_OTHER_SIREN: SuggestionAction.ENRICH_ACTEURS_CLOSED,
        COHORTS.CLOSED_REP_SAME_SIREN: SuggestionAction.ENRICH_ACTEURS_CLOSED,
        COHORTS.RGPD: SuggestionAction.ENRICH_ACTEURS_RGPD,
        COHORTS.VILLES_TYPO: SuggestionAction.ENRICH_ACTEURS_VILLES_TYPO,
        COHORTS.VILLES_NEW: SuggestionAction.ENRICH_ACTEURS_VILLES_NEW,
        COHORTS.ACTEUR_CP_TYPO: SuggestionAction.ENRICH_ACTEURS_CP_TYPO,
        COHORTS.REVISION_ACTEUR_CP_TYPO: (
            SuggestionAction.ENRICH_REVISION_ACTEURS_CP_TYPO
        ),
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
            logger.info(f"Interprétation de {cohort=}")
            change_preparation_function = COHORTS_TO_PREPARE_CHANGES[cohort]
            changes, contexte = change_preparation_function(row)
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
