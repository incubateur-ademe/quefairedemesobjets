import logging

import pandas as pd
from crawl.config.columns import COLS
from crawl.config.constants import LABEL_URL_ORIGINE, LABEL_URL_PROPOSEE
from utils import logging_utils as log
from utils.dataframes import (
    df_col_assert_get_unique,
    df_col_count_lists,
    df_none_or_empty,
)
from utils.django import django_setup_full

logger = logging.getLogger(__name__)

django_setup_full()


def suggestions_metadata(
    df: pd.DataFrame,
) -> dict[str, int]:
    """Calculates metadata for the suggestions cohort"""
    meta = {}
    cohort = df[COLS.COHORT].iloc[0]

    meta[f"{cohort}: # URLs"] = len(df)
    meta[f"{cohort}: # Acteurs"] = df_col_count_lists(df=df, col=COLS.ACTEURS)

    df_meta = pd.DataFrame(list(meta.items()), columns=["Cas de figure", "Nombre"])
    logger.info(f"Metadata de la cohorte {cohort}:")
    logger.info("\n" + df_meta.to_markdown(index=False))
    return meta


def suggestions_prepare(
    df: pd.DataFrame,
) -> list[dict]:
    """Generate suggestions for URL updates:
    - df_crawl_ok_diff = successful AND different = propose
    - df_crawl_fail = failed = propose None"""
    from data.models.change import SuggestionChange
    from data.models.changes import ChangeActeurUpdateRevision

    if df_none_or_empty(df):
        return []

    cohorte = df_col_assert_get_unique(df, COLS.COHORT)

    suggestions = []
    for _, row in df.iterrows():
        changes = []
        for acteur in row[COLS.ACTEURS]:
            change = SuggestionChange(
                order=1,
                reason=row[COLS.COHORT],
                model_name=ChangeActeurUpdateRevision.name(),
                model_params={
                    "id": acteur[COLS.ID],
                    "data": {COLS.URL_DB: row[COLS.SUGGEST_VALUE]},
                },
            ).model_dump()
            changes.append(change)
        url_original = row[COLS.URL_ORIGIN]
        url_proposed = row[COLS.SUGGEST_VALUE]
        if url_original == url_proposed:
            msg = f"""URL originale & proposée identiques: {url_original},
            on devrait pas avoir de suggestion"""
            raise ValueError(msg)
        suggestions.append(
            {
                "contexte": {
                    LABEL_URL_ORIGINE: url_original,
                    LABEL_URL_PROPOSEE: url_proposed,
                },
                "suggestion": {
                    "title": row[COLS.COHORT],
                    "changes": changes,
                },
            }
        )

    logger.info(log.banner_string(f"🏁 Résultat pour {cohorte=}"))
    logger.info(f"Suggestion générées: {len(suggestions)}")
    for s in suggestions:
        title = s["suggestion"]["title"]
        url = s["contexte"][LABEL_URL_ORIGINE]
        log.preview(f"{title}: {url=}", s)

    return suggestions


def crawl_urls_suggestions_to_db(
    metadata: dict,
    suggestions: list[dict],
    identifiant_action: str,
    identifiant_execution: str,
) -> None:
    """Writing suggestions to DB"""

    logger.info(f"{identifiant_action=}")
    logger.info(f"{identifiant_execution=}")

    from data.models.suggestion import (
        Suggestion,
        SuggestionAction,
        SuggestionCohorte,
        SuggestionStatut,
    )

    cohorte = SuggestionCohorte(
        identifiant_action=identifiant_action,
        identifiant_execution=identifiant_execution,
        type_action=SuggestionAction.CRAWL_URLS,
        statut=SuggestionStatut.AVALIDER,
        metadata=metadata,
    )
    cohorte.save()

    for sugg in suggestions:
        url = sugg["contexte"][LABEL_URL_ORIGINE]
        log.preview(f"Suggestion pour {url=}", sugg)
        Suggestion(
            suggestion_cohorte=cohorte,
            statut=SuggestionStatut.AVALIDER,
            contexte=sugg["contexte"],
            suggestion=sugg["suggestion"],
        ).save()


def crawl_urls_suggest(
    df: pd.DataFrame, dag_display_name: str, run_id: str, dry_run: bool = True
) -> int:
    """Main function to generate suggestions for URLs"""
    if df_none_or_empty(df):
        raise ValueError("DF vide ou None on devrait pas être là")

    cohort = df_col_assert_get_unique(df, COLS.COHORT)

    log.preview_df_as_markdown("df d'entrée", df)

    metadata = suggestions_metadata(df)
    suggestions = suggestions_prepare(df)
    written_to_db_count = 0

    logger.info(log.banner_string("✍️ Ecritures en DB"))
    if dry_run:
        logger.info(f"{dry_run=}, on ne fait pas")
    else:
        crawl_urls_suggestions_to_db(
            metadata=metadata,
            suggestions=suggestions,
            identifiant_action=f"{dag_display_name} - {cohort}",
            identifiant_execution=f"{run_id}",
        )
        written_to_db_count = len(suggestions)
    return written_to_db_count
