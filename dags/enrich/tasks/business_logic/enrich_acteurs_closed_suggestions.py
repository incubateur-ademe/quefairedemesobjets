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

    # Validation
    if df is None or df.empty:
        raise ValueError("df vide: on devrait pas être ici")

    if cohort_type not in [
        COHORTS.ACTEURS_CLOSED_NOT_REPLACED,
        COHORTS.ACTEURS_CLOSED_REP_DIFF_SIREN,
        COHORTS.ACTEURS_CLOSED_REP_SAME_SIREN,
    ]:
        raise ValueError(f"Mauvaise cohorte: {cohort_type=}")

    # Suggestions
    suggestions = []
    for _, row in df.iterrows():
        row = dict(row)

        # -----------------------------------------
        # NOT REPLACED
        # -----------------------------------------
        if cohort_type == COHORTS.ACTEURS_CLOSED_NOT_REPLACED:
            changes = []
            model_params = {
                "id": row[COLS.ACTEUR_ID],
                "data": {
                    "statut": ActeurStatus.INACTIF,
                    "siret_is_closed": True,
                    "acteur_type": row[COLS.ACTEUR_TYPE],
                    "source": row[COLS.ACTEUR_SOURCE],
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
        # REPLACED
        # -----------------------------------------
        elif cohort_type in [
            COHORTS.ACTEURS_CLOSED_REP_DIFF_SIREN,
            COHORTS.ACTEURS_CLOSED_REP_SAME_SIREN,
        ]:
            cohortes = df[COLS.REMPLACER_COHORTE].unique()
            if len(cohortes) > 1:
                raise ValueError(f"Une seule cohorte à la fois: {cohortes=}")
            logger.info(f"{cohort_type}: suggestion acteur id={row[COLS.ACTEUR_ID]}")

            changes = []

            # Parent
            parent_id = parent_id_generate([str(row[COLS.REMPLACER_SIRET])])
            model_params = {
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
                    "acteur_type": row[COLS.ACTEUR_TYPE],
                    "source": None,
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
                "id": row[COLS.ACTEUR_ID],
                "data": {
                    "statut": ActeurStatus.INACTIF,
                    "parent": parent_id,
                    "parent_reason": (
                        f"SIRET {row[COLS.ACTEUR_SIRET]} "
                        f"détecté le {today} comme fermé dans AE, "
                        f"remplacé par SIRET {row[COLS.REMPLACER_SIRET]}"
                    ),
                    "siret_is_closed": True,
                    "acteur_type": row[COLS.ACTEUR_TYPE],
                    "source": row[COLS.ACTEUR_SOURCE],
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

        else:
            raise ValueError(f"Mauvaise cohorte: {cohort_type=}")

        # Generic to all cohorts
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
        identifiant_execution=f"{cohort_type}",
        statut=SuggestionStatut.AVALIDER,
        type_action=SuggestionAction.ENRICH_ACTEURS_CLOSED,
        metadata={"🔢 Nombre de suggestions": len(suggestions)},
    )
    cohort.save()
    for suggestion in suggestions:
        Suggestion(
            suggestion_cohorte=cohort,
            statut=SuggestionStatut.AVALIDER,
            contexte=suggestion["contexte"],
            suggestion=suggestion["suggestion"],
        ).save()
