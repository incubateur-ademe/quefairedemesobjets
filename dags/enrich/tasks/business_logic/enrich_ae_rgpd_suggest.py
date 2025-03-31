"""Generate suggestions from matches"""

import logging
from typing import Any

import pandas as pd
from enrich.config import COLS
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


# TODO: create a utility + model which helps us generate
# structured & consistent details for generic_suggestion_details.html
def sumline(label: str, value: Any, value_type: str):
    return locals()


def enrich_ae_rgpd_suggest(
    df: pd.DataFrame,
    identifiant_action: str,
    identifiant_execution: str,
    dry_run: bool = True,
) -> list[dict]:
    """Generate suggestions from matches"""
    from data.models import (
        Suggestion,
        SuggestionAction,
        SuggestionCohorte,
        SuggestionStatut,
    )
    from data.models.change import SuggestionChange
    from data.models.changes.acteur_rgpd_anonymize import (
        ACTEUR_FIELDS_TO_ANONYMIZE,
        ChangeActeurRgpdAnonymize,
    )

    # Prepare suggestions
    suggestions = []
    for _, row in df.iterrows():
        changes = []

        # Preparing & validating the change params
        acteur_id = row[COLS.ACTEUR_ID]
        model_params = {"id": acteur_id}
        ChangeActeurRgpdAnonymize(**model_params).validate()

        # Preparing suggestion with change and ensuring we can JSON serialize it
        change = SuggestionChange(
            order=1,
            reason="Noms/prénoms détectés dans l'Annuaire Entreprise (AE)",
            entity_type="acteur_displayed",
            model_name=ChangeActeurRgpdAnonymize.name(),
            model_params=model_params,
        ).model_dump()
        changes.append(change)
        contexte_changes = ACTEUR_FIELDS_TO_ANONYMIZE.copy()
        contexte_changes["commentaires"] = "➕ Ajout mention avec 📆 date & ⏰ heure"
        suggestion = {
            "contexte": {
                "changements": contexte_changes,
            },
            "suggestion": {
                "title": "🕵️ Anonymisation RGPD",
                "summary": [
                    sumline("noms d'origine", row[COLS.ACTEUR_NOMS_ORIGINE], "text"),
                    sumline("mots de match", row[COLS.MATCH_WORDS], "text_list"),
                    sumline(
                        "score de match", row[COLS.MATCH_SCORE_AE_RGPD], "score_0_to_1"
                    ),
                    sumline("changements", "voir contexte/détails", "text"),
                ],
                "changes": changes,
            },
        }
        suggestions.append(suggestion)
        log.preview(f"Suggestion pour acteur: {acteur_id}", suggestion)

    # Saving suggestions
    logging.info(log.banner_string("✍️ Ecritures en DB"))
    if dry_run:
        logger.info("✋ Dry run: suggestions pas écrites en base")
    else:
        cohort = SuggestionCohorte(
            identifiant_action=identifiant_action,
            identifiant_execution=identifiant_execution,
            type_action=SuggestionAction.RGPD_ANONYMIZE,
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

    return suggestions
