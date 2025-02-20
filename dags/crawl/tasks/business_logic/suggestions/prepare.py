import logging

import pandas as pd
from crawl.config.constants import (
    COL_URL_DB,
    COL_URL_ORIGINAL,
    COL_URL_SUCCESS,
    COL_URLS_RESULTS,
    LABEL_SCENARIO,
    LABEL_URL_ORIGINE,
    LABEL_URL_PROPOSEE,
    SCENARIO_FAIL,
    SCENARIO_OK_DIFF,
)
from sources.config.shared_constants import EMPTY_ACTEUR_FIELD
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def crawl_urls_suggestions_prepare(
    df_ok_diff: pd.DataFrame, df_fail: pd.DataFrame
) -> list[dict]:
    """Generate suggestions for URL updates:
    - df_ok_diff = successful AND different = propose
    - df_fail = failed = propose None"""
    from data.models.change import SuggestionChange
    from data.models.changes import ChangeActeurUpdateData

    suggestions = []

    df_ok_diff["suggest_value"] = df_ok_diff[COL_URL_SUCCESS]
    df_ok_diff["suggest_scenario"] = SCENARIO_OK_DIFF
    df_fail["suggest_value"] = EMPTY_ACTEUR_FIELD
    df_fail["suggest_scenario"] = SCENARIO_FAIL
    df = pd.concat([df_ok_diff, df_fail])

    for _, row in df.iterrows():
        changes = []
        for acteur in row["acteurs"]:
            change = SuggestionChange(
                order=1,
                reason="URL update",
                entity_type="acteur_displayed",
                model_name=ChangeActeurUpdateData.name(),
                model_params={
                    "id": acteur["identifiant_unique"],
                    "data": {COL_URL_DB: row["suggest_value"]},
                },
            )
            changes.append(change.model_dump())
        url_original = row[COL_URL_ORIGINAL]
        url_proposed = row["suggest_value"]
        result = row[COL_URLS_RESULTS][-1]
        if url_original == url_proposed:
            msg = f"""URL originale & proposée identiques: {url_original},
            on devrait pas avoir de suggestion"""
            raise ValueError(msg)
        suggestions.append(
            {
                "contexte": {
                    LABEL_SCENARIO: row["suggest_scenario"],
                    LABEL_URL_ORIGINE: url_original,
                    LABEL_URL_PROPOSEE: url_proposed,
                },
                "suggestion": {
                    "scenario": row["suggest_scenario"],
                    "reason": "reason",
                    "reason_was_success": result["was_success"],
                    "reason_code": result["status_code"],
                    "reason_error": result["error"],
                    "url_original": url_original,
                    "url_proposed": url_proposed,
                    "changes": changes,
                },
            }
        )

    logging.info(log.banner_string("🏁 Résultat final de cette tâche"))
    logger.info(f"Suggestion générées: {len(suggestions)}")
    for s in suggestions:
        scenario = s["contexte"]["Scénario"]
        url = s["contexte"][LABEL_URL_ORIGINE]
        log.preview(f"{scenario}: {url=}", s)

    return suggestions
