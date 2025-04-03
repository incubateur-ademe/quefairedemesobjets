import logging

import pandas as pd
from enrich.config import COHORTS

logger = logging.getLogger(__name__)


def enrich_ae_suggestions(
    df: pd.DataFrame,
    cohort_type: str,
    identifiant_action: str,
    identifiant_execution: str,
    dry_run: bool = True,
) -> None:
    from data.models import (
        Suggestion,
        SuggestionAction,
        SuggestionCohorte,
        SuggestionStatut,
    )
    from data.models.change import SuggestionChange
    from data.models.changes import ChangeActeurUpdateData
    from qfdmo.models import ActeurStatus

    if cohort_type not in [
        COHORTS.ACTEURS_CLOSED_NOT_REPLACED,
        COHORTS.ACTEURS_CLOSED_REP_DIFF_SIREN,
        COHORTS.ACTEURS_CLOSED_REP_SAME_SIREN,
    ]:
        raise ValueError(f"Mauvaise cohorte: {cohort_type=}")

    suggestions = []

    for row in df.itertuples(index=False):

        # -----------------------------------------
        # CHANGES: PREPARE
        # -----------------------------------------
        changes = []

        model_params = {
            "id": row.acteur_id,
            "data": {
                "statut": ActeurStatus.INACTIF,
            },
        }
        ChangeActeurUpdateData(**model_params).validate()
        change = SuggestionChange(
            order=1,
            reason=cohort_type,
            entity_type="acteur_displayed",
            model_name=ChangeActeurUpdateData.name(),
            model_params=model_params,
        ).model_dump()
        changes.append(change)

        # -----------------------------------------
        # SUGGESTION: PREPARE
        # -----------------------------------------
        suggestions.append(
            {
                # TODO: free format thanks to recursive model
                "contexte": {},
                "suggestion": {
                    "title": cohort_type,
                    "summary": [],
                    "changes": changes,
                },
            }
        )

    # -----------------------------------------
    # DRY RUN: STOP HERE
    # -----------------------------------------
    if dry_run:
        logger.info("✋ Dry run: suggestions pas écrites en base")
        return

    # -----------------------------------------
    # SUGGESTION: WRITE TO DB
    # -----------------------------------------
    cohort = SuggestionCohorte(
        identifiant_action=identifiant_action,
        identifiant_execution=f"{cohort_type} {identifiant_execution}",
        statut=SuggestionStatut.AVALIDER,
        type_action=SuggestionAction.ACTEURS_CLOSED,
        metadata={"🔢 Nombre de suggestions": len(suggestions)},
    )
    cohort.save()
    for suggestion in suggestions:

        for suggestion in suggestions:
            Suggestion(
                suggestion_cohorte=cohort,
                statut=SuggestionStatut.AVALIDER,
                contexte=suggestion["contexte"],
                suggestion=suggestion["suggestion"],
            ).save()
