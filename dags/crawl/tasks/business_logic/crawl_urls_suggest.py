import logging

import pandas as pd
from crawl.config.columns import COLS
from crawl.config.constants import LABEL_URL_ORIGINE, LABEL_URL_PROPOSEE
from utils import logging_utils as log
from utils.dataframes import df_col_assert_get_unique, df_none_or_empty
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
    meta[f"{cohort}: # Acteurs"] = df[COLS.COUNT].sum()

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
):
    """Main function to generate suggestions for URLs"""

    from data.models.suggestion import (
        SuggestionAction,
        SuggestionCohorte,
        SuggestionGroupe,
        SuggestionUnitaire,
    )
    from qfdmo.models.acteur import Acteur, RevisionActeur

    if df_none_or_empty(df):
        raise ValueError("DF vide ou None on devrait pas être là")

    cohort_label = df_col_assert_get_unique(df, COLS.COHORT)

    log.preview_df_as_markdown("df d'entrée", df)

    # 1. Create a SuggestionCohorte (same as today)
    identifiant_action = f"{dag_display_name} - {cohort_label}"
    identifiant_execution = f"{run_id}"
    metadata = suggestions_metadata(df)
    logging.warning(f"{identifiant_action=}")
    logging.warning(f"{identifiant_execution=}")
    logging.warning(f"{SuggestionAction.CRAWL_URLS=}")
    logging.warning(f"{metadata=}")

    metadata = {}
    cohort = SuggestionCohorte(
        identifiant_action=identifiant_action,
        identifiant_execution=identifiant_execution,
        type_action=SuggestionAction.CRAWL_URLS,
        metadata={k: v for k, v in metadata.items()},
    )
    cohort.save()

    # 2. Create a SuggestionGroupe by url to update

    for _, row in df.iterrows():
        suggestion_groupe = SuggestionGroupe(
            suggestion_cohorte=cohort,
            contexte={
                COLS.URL_ORIGIN: row[COLS.URL_ORIGIN],
                COLS.SUGGEST_VALUE: row[COLS.SUGGEST_VALUE],
            },
            metadata={
                "nb d'acteurs impactés": row[COLS.COUNT],
            },
        )
        suggestion_groupe.save()

        # 3. Create a SuggestionUnitaire by acteur/revision to update

        # get all acteur without revision
        revision_acteurs = RevisionActeur.objects.filter(url=row[COLS.URL_ORIGIN])
        for revision_acteur in revision_acteurs:
            SuggestionUnitaire(
                suggestion_groupe=suggestion_groupe,
                revision_acteur=revision_acteur,
                suggestion_modele="RevisionActeur",
                champs=[COLS.URL_ORIGIN],
                valeurs=[row[COLS.SUGGEST_VALUE]],
            ).save()
        acteurs = Acteur.objects.filter(url=row[COLS.URL_ORIGIN])
        for acteur in acteurs:
            # Check that url is not overridden by a revision
            revision = RevisionActeur.objects.filter(
                identifiant_unique=acteur.identifiant_unique
            ).first()
            if revision and not revision.url:
                SuggestionUnitaire(
                    suggestion_groupe=suggestion_groupe,
                    acteur=acteur,
                    suggestion_modele="Acteur",
                    champs=[COLS.URL_ORIGIN],
                    valeurs=[row[COLS.SUGGEST_VALUE]],
                ).save()
