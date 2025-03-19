"""Generate suggestions from matches"""

import logging

import pandas as pd
from enrich.config import COLS
from sources.config.shared_constants import INFO_TO_HIDE
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


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
    from data.models.changes import ChangeActeurUpdateData
    from qfdmo.models import Acteur

    # Acteur fields
    field_nom = Acteur._meta.get_field("nom").name
    field_nom_officiel = Acteur._meta.get_field("nom_officiel").name
    field_nom_commercial = Acteur._meta.get_field("nom_commercial").name

    # Prepare suggestions
    suggestions = []
    for _, row in df.iterrows():
        changes = []

        # Preparing & validating the change params
        acteur_id = row[COLS.ACTEUR_ID]
        model_params = {
            "id": acteur_id,
            "data": {
                field_nom: INFO_TO_HIDE,
                field_nom_officiel: INFO_TO_HIDE,
                field_nom_commercial: INFO_TO_HIDE,
            },
        }
        ChangeActeurUpdateData(**model_params).validate()

        # Preparing suggestion with change and ensuring we can JSON serialize it
        change = SuggestionChange(
            order=1,
            reason="Noms/prénoms détectés dans l'Annuaire Entreprise (AE)",
            entity_type="acteur_displayed",
            model_name=ChangeActeurUpdateData.name(),
            model_params=model_params,
        ).model_dump()
        changes.append(change)
        suggestion = {
            "contexte": "Idem suggestion",
            "suggestion": {
                "title": "🕵️ RGPD: anonymiser les noms des acteurs",
                "summary": {
                    "noms d'origine": row[COLS.ACTEUR_NOMS_ORIGINE],
                    "mots de match": row[COLS.MATCH_WORDS],
                    "score de match": row[COLS.MATCH_SCORE],
                    "changement": f"""{field_nom} & {field_nom_officiel} &
                    {field_nom_commercial} -> {INFO_TO_HIDE}""",
                },
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
