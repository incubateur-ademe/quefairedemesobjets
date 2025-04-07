import logging
from datetime import datetime, timezone

import pandas as pd
from cluster.tasks.business_logic.cluster_acteurs_parents_choose_new import (
    parent_id_generate,
)
from enrich.config import COHORTS, COLS

logger = logging.getLogger(__name__)


def enrich_acteurs_closed_suggestions(
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
    from data.models.changes import ChangeActeurCreateAsParent, ChangeActeurUpdateData
    from qfdmo.models import ActeurStatus

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if cohort_type not in [
        COHORTS.ACTEURS_CLOSED_NOT_REPLACED,
        COHORTS.ACTEURS_CLOSED_REP_DIFF_SIREN,
        COHORTS.ACTEURS_CLOSED_REP_SAME_SIREN,
    ]:
        raise ValueError(f"Mauvaise cohorte: {cohort_type=}")

    suggestions = []

    for _, row in df.iterrows():
        row = row._asdict()

        # -----------------------------------------
        # NOT REPLACED
        # -----------------------------------------
        if cohort_type == COHORTS.ACTEURS_CLOSED_NOT_REPLACED:
            raise NotImplementedError("Pas encore implémenté")

        # -----------------------------------------
        # REPLACED
        # -----------------------------------------
        elif cohort_type not in [
            COHORTS.ACTEURS_CLOSED_REP_DIFF_SIREN,
            COHORTS.ACTEURS_CLOSED_REP_SAME_SIREN,
        ]:
            cohorts = row[COLS.REMPLACER_COHORTE].unique()
            if len(cohorts) > 1:
                raise ValueError(f"Une seule cohorte à la fois: {cohorts=}")

            changes = []

            # Parent
            parent_id = parent_id_generate([row[COLS.REMPLACER_SIRET]])
            model_params = {
                "id": parent_id,
                "data": {
                    "nom": row[COLS.REMPLACER_NOM],
                    "adresse": row[COLS.REMPLACER_ADRESSE],
                    "code_postal": row[COLS.REMPLACER_CODE_POSTAL],
                    "ville": row[COLS.REMPLACER_VILLE],
                    "siren": row[COLS.REMPLACER_SIRET][:9],
                    "siret": row[COLS.REMPLACER_SIRET],
                    "naf": row[COLS.REMPLACER_NAF],
                },
            }
            ChangeActeurCreateAsParent(**model_params).validate()
            change = SuggestionChange(
                order=1,
                reason=cohort_type,
                entity_type="acteur_displayed",
                model_name=ChangeActeurCreateAsParent.name(),
                model_params=model_params,
            ).model_dump()
            changes.append(change)

            # Child
            model_params = {
                "id": row.acteur_id,
                "data": {
                    "statut": ActeurStatus.INACTIF,
                    "parent_id": parent_id,
                    "parent_reason": f"""SIRET {row.acteur_siret} détecté le {today}
                    comme fermé dans AE, remplacé par SIRET {row.remplacer_siret}""",
                    "siret_is_closed": True,
                },
            }
            ChangeActeurUpdateData(**model_params).validate()
            change = SuggestionChange(
                order=2,
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
