import logging
from datetime import datetime, timezone

import pandas as pd
from cluster.tasks.business_logic.cluster_acteurs_parents_choose_new import (
    parent_id_generate,
)
from enrich.config import COHORTS, COLS, Cohort

logger = logging.getLogger(__name__)


def enrich_dbt_model_to_suggestions(
    df: pd.DataFrame,
    cohort: Cohort,
    identifiant_action: str,
    dry_run: bool = True,
) -> bool:
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

    if cohort.code not in [
        COHORTS.CLOSED_NOT_REPLACED.code,
        COHORTS.CLOSED_REP_OTHER_SIREN.code,
        COHORTS.CLOSED_REP_SAME_SIREN.code,
    ]:
        raise ValueError(f"Mauvaise cohorte: {cohort=}")

    # Suggestions
    suggestions = []
    for _, row in df.iterrows():
        row = dict(row)

        # -----------------------------------------
        # NOT REPLACED
        # -----------------------------------------
        if cohort == COHORTS.CLOSED_NOT_REPLACED:
            changes = []
            model_params = {
                "id": row[COLS.ACTEUR_ID],
                "data": {
                    "identifiant_unique": row[COLS.ACTEUR_ID],
                    "statut": ActeurStatus.INACTIF,
                    # TODO: fix inconsistency between acteur_siret and siret
                    # in non-replaced model
                    "siret": row[COLS.SIRET],
                    "siret_is_closed": True,
                    "acteur_type": row[COLS.ACTEUR_TYPE_ID],
                    "source": row[COLS.ACTEUR_SOURCE_ID],
                },
            }
            ChangeActeurUpdateData(**model_params).validate()
            change = SuggestionChange(
                order=1,
                reason="SIRET & SIREN fermés, 0 remplacement trouvé",
                entity_type="acteur_displayed",
                model_name=ChangeActeurUpdateData.name(),
                model_params=model_params,
            ).model_dump()
            changes.append(change)

        # -----------------------------------------
        # REPLACED
        # -----------------------------------------
        elif cohort in [
            COHORTS.CLOSED_REP_OTHER_SIREN,
            COHORTS.CLOSED_REP_SAME_SIREN,
        ]:
            cohorts = df[COLS.SUGGEST_COHORT_CODE].unique()
            if len(cohorts) > 1:
                raise ValueError(f"Une seule cohorte à la fois: {cohorts=}")
            if cohorts[0] != cohort.code:
                raise ValueError(f"Mauvaise cohorte: {cohorts=} != {cohort=}")
            logger.info(f"{cohort.label}: suggestion acteur id={row[COLS.ACTEUR_ID]}")

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
                    "acteur_type": row[COLS.ACTEUR_TYPE_ID],
                    "source": None,
                    "statut": ActeurStatus.ACTIF,
                },
            }
            ChangeActeurCreateAsParent(**model_params).validate()
            change = SuggestionChange(
                order=1,
                reason="besoin d'un parent pour nouvel acteur",
                entity_type="acteur_displayed",
                model_name=ChangeActeurCreateAsParent.name(),
                model_params=model_params,
            ).model_dump()
            changes.append(change)

            # Child
            model_params = {
                "id": row[COLS.ACTEUR_ID],
                "data": {
                    "identifiant_unique": row[COLS.ACTEUR_ID],
                    "parent": parent_id,
                    "parent_reason": (
                        f"SIRET {row[COLS.ACTEUR_SIRET]} "
                        f"détecté le {today} comme fermé dans AE, "
                        f"remplacé par SIRET {row[COLS.REMPLACER_SIRET]}"
                    ),
                    "siren": row[COLS.ACTEUR_SIRET][:9],
                    "siret": row[COLS.ACTEUR_SIRET],
                    "siret_is_closed": True,
                    "acteur_type": row[COLS.ACTEUR_TYPE_ID],
                    "source": row[COLS.ACTEUR_SOURCE_ID],
                    "statut": ActeurStatus.INACTIF,
                },
            }
            ChangeActeurUpdateData(**model_params).validate()
            change = SuggestionChange(
                order=2,
                reason="rattaché au parent",
                entity_type="acteur_displayed",
                model_name=ChangeActeurUpdateData.name(),
                model_params=model_params,
            ).model_dump()
            changes.append(change)

        else:
            raise ValueError(f"Mauvaise cohorte: {cohort=}")

        # Generic to all cohorts
        suggestions.append(
            {
                # TODO: free format thanks to recursive model
                "contexte": {},
                "suggestion": {
                    "title": cohort.label,
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
