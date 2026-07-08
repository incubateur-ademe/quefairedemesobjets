"""Generate SuggestionGroupe/SuggestionUnitaire for SIRET/SIREN enrichment.

Unlike the legacy suggestions (1 Suggestion per acteur), we group acteurs into
1 SuggestionGroupe per proposed SIRET (resp. per acteur SIRET) and 1
SuggestionUnitaire per acteur, the same way crawl_urls does with
`use_legacy_suggestions=False`.
"""

import logging

import pandas as pd
from enrich.config.columns import COLS
from enrich.tasks.business_logic.enrich_dbt_model_read import enrich_dbt_model_read
from utils import logging_utils as log
from utils.django import django_setup_full

logger = logging.getLogger(__name__)


def _est_parent_par_acteur(identifiants: list[str]) -> dict[str, bool]:
    """Returns a {identifiant_unique: est_parent} map for the given acteurs."""
    from qfdmo.models import VueActeur

    return dict(
        VueActeur.objects.filter(identifiant_unique__in=identifiants).values_list(
            "identifiant_unique", "est_parent"
        )
    )


def enrich_siret_siren_to_suggestion_groupes(
    df: pd.DataFrame,
    cohort: str,
    suggest_action: str,
    suggest_field: str,
    identifiant_action: str,
    dry_run: bool = True,
) -> bool:
    """Write 1 SuggestionGroupe per `suggest_field` value and 1
    SuggestionUnitaire per acteur, suggesting `suggest_field`."""
    django_setup_full()
    from data.models.suggestion import (
        SuggestionAction,
        SuggestionCohorte,
        SuggestionGroupe,
        SuggestionStatut,
        SuggestionUnitaire,
    )

    if df is None or df.empty:
        raise ValueError("df vide: on devrait pas être ici")

    # Only keep acteurs that actually exist & know which are parents
    identifiants = list(df[COLS.IDENTIFIANT_UNIQUE].unique())
    est_parent_map = _est_parent_par_acteur(identifiants)
    df = df[df[COLS.IDENTIFIANT_UNIQUE].isin(est_parent_map.keys())]
    if df.empty:
        logger.info("Aucun acteur visible correspondant, rien à suggérer")
        return False

    nb_groupes = df[suggest_field].nunique()
    nb_acteurs = len(df)
    metadata = {
        f"{cohort}: # {suggest_field}": nb_groupes,
        f"{cohort}: # Acteurs": nb_acteurs,
    }
    logger.info(log.banner_string(f"🏁 Cohorte {cohort}"))
    logger.info(f"{metadata=}")

    # -----------------------------------------
    # DRY RUN: STOP HERE
    # -----------------------------------------
    if dry_run:
        logger.info("✋ Dry run: suggestions pas écrites en base")
        return False

    # -----------------------------------------
    # WRITE TO DB
    # -----------------------------------------
    cohorte = SuggestionCohorte(
        identifiant_action=identifiant_action,
        identifiant_execution=f"{cohort}",
        type_action=getattr(SuggestionAction, suggest_action),
        statut=SuggestionStatut.AVALIDER,
        metadata=metadata,
    )
    cohorte.save()

    from django.db import transaction
    from qfdmo.models import RevisionActeur

    for group_value, group_df in df.groupby(suggest_field):
        with transaction.atomic():
            suggestion_groupe = SuggestionGroupe.objects.create(
                suggestion_cohorte=cohorte,
                statut=SuggestionStatut.AVALIDER,
                contexte={
                    suggest_field: group_value,
                    "# acteurs": len(group_df),
                },
            )
            for _, row in group_df.iterrows():
                identifiant_unique = row[COLS.IDENTIFIANT_UNIQUE]
                est_parent = est_parent_map.get(identifiant_unique, False)
                parent_revision = None
                suggestion_modele = "RevisionActeur"
                if est_parent:
                    parent_revision = RevisionActeur.objects.get(
                        identifiant_unique=identifiant_unique
                    )
                    suggestion_modele = "ParentRevisionActeur"

                SuggestionUnitaire.objects.create(
                    suggestion_groupe=suggestion_groupe,
                    statut=SuggestionStatut.AVALIDER,
                    revision_acteur_id=(
                        identifiant_unique
                        if suggestion_modele == "RevisionActeur"
                        else None
                    ),
                    parent_revision_acteur=parent_revision,
                    suggestion_modele=suggestion_modele,
                    raison=cohort,
                    champs=[suggest_field],
                    valeurs=[str(row[suggest_field])],
                )

    return True


def enrich_siret_siren_suggest(
    dbt_model_name: str,
    cohort: str,
    suggest_action: str,
    suggest_field: str,
    identifiant_action: str,
    dry_run: bool = True,
) -> bool:
    """Reads a DBT model and generates grouped suggestions for it"""
    df = enrich_dbt_model_read(dbt_model_name)

    if df.empty:
        logger.info(f"0 donnée pour {dbt_model_name=}")
        return False

    return enrich_siret_siren_to_suggestion_groupes(
        df=df,
        cohort=cohort,
        suggest_action=suggest_action,
        suggest_field=suggest_field,
        identifiant_action=identifiant_action,
        dry_run=dry_run,
    )
