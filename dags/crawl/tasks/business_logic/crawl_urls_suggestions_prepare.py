import logging

import pandas as pd
from crawl.config.constants import (
    COL_ACTEURS,
    COL_ID,
    COL_SCENARIO,
    COL_SUGGEST_VALUE,
    COL_URL_DB,
    COL_URL_ORIGINAL,
    COL_URL_SUCCESS,
    LABEL_SCENARIO,
    LABEL_URL_ORIGINE,
    LABEL_URL_PROPOSEE,
    SCENARIO_DNS_FAIL,
    SCENARIO_SYNTAX_FAIL,
    SCENARIO_URL_FAIL,
    SCENARIO_URL_OK_DIFF,
)
from sources.config.shared_constants import EMPTY_ACTEUR_FIELD
from utils import logging_utils as log
from utils.django import django_setup_full

django_setup_full()

logger = logging.getLogger(__name__)


def df_not_empty(df: pd.DataFrame) -> bool:
    return df is not None and not df.empty


def crawl_urls_suggestions_prepare(
    df_syntax_fail: pd.DataFrame,
    df_dns_fail: pd.DataFrame,
    df_urls_ok_diff: pd.DataFrame,
    df_urls_fail: pd.DataFrame,
) -> list[dict]:
    """Generate suggestions for URL updates:
    - df_urls_ok_diff = successful AND different = propose
    - df_urls_fail = failed = propose None"""
    from data.models.change import SuggestionChange
    from data.models.changes import ChangeActeurUpdateData

    suggestions = []
    dfs = []

    if df_not_empty(df_syntax_fail):
        df_syntax_fail[COL_SCENARIO] = SCENARIO_SYNTAX_FAIL
        df_syntax_fail[COL_SUGGEST_VALUE] = EMPTY_ACTEUR_FIELD
        dfs.append(df_syntax_fail)

    if df_not_empty(df_dns_fail):
        df_dns_fail[COL_SCENARIO] = SCENARIO_DNS_FAIL
        df_dns_fail[COL_SUGGEST_VALUE] = EMPTY_ACTEUR_FIELD
        dfs.append(df_dns_fail)

    if df_not_empty(df_urls_ok_diff):
        df_urls_ok_diff[COL_SCENARIO] = SCENARIO_URL_OK_DIFF
        df_urls_ok_diff[COL_SUGGEST_VALUE] = df_urls_ok_diff[COL_URL_SUCCESS]
        dfs.append(df_urls_ok_diff)

    if df_not_empty(df_urls_fail):
        df_urls_fail[COL_SCENARIO] = SCENARIO_URL_FAIL
        df_urls_fail[COL_SUGGEST_VALUE] = EMPTY_ACTEUR_FIELD
        dfs.append(df_urls_fail)

    if not dfs:
        raise ValueError(
            """On devrait pas arriver à la tâche de préparation des suggestions
            si on a 0 suggestion à traiter, la tâche metadata
            devrait générer un skip"""
        )

    df = pd.concat(dfs)

    for _, row in df.iterrows():
        changes = []
        for acteur in row[COL_ACTEURS]:
            change = SuggestionChange(
                order=1,
                reason=row[COL_SCENARIO],
                entity_type="acteur_displayed",
                model_name=ChangeActeurUpdateData.name(),
                model_params={
                    "id": acteur[COL_ID],
                    "data": {COL_URL_DB: row[COL_SUGGEST_VALUE]},
                },
            )
            changes.append(change.model_dump())
        url_original = row[COL_URL_ORIGINAL]
        url_proposed = row[COL_SUGGEST_VALUE]
        if url_original == url_proposed:
            msg = f"""URL originale & proposée identiques: {url_original},
            on devrait pas avoir de suggestion"""
            raise ValueError(msg)
        suggestions.append(
            {
                "contexte": {
                    LABEL_SCENARIO: row[COL_SCENARIO],
                    LABEL_URL_ORIGINE: url_original,
                    LABEL_URL_PROPOSEE: url_proposed,
                },
                "suggestion": {
                    "scenario": row[COL_SCENARIO],
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
