"""Generate SuggestionGroupe/SuggestionUnitaire for lien succession enrichments.

Acteurs are grouped by the full replacement mapping:
(source SIREN, source SIRET) -> (target SIREN, target SIRET).
"""

import logging

import pandas as pd
from enrich.config.columns import COLS
from enrich.tasks.business_logic.enrich_dbt_model_read import enrich_dbt_model_read
from utils import logging_utils as log
from utils.django import django_setup_full

logger = logging.getLogger(__name__)

GROUP_KEYS = [
    COLS.SIREN_ACTUEL,
    COLS.SIRET_ACTUEL,
    COLS.SIREN_SUCCESSEUR,
    COLS.SIRET_SUCCESSEUR,
]
SUGGEST_FIELDS = [COLS.SIREN, COLS.SIRET]
SUGGEST_VALUES = [COLS.SIREN_SUCCESSEUR, COLS.SIRET_SUCCESSEUR]


def _est_parent_par_acteur(identifiants: list[str]) -> dict[str, bool]:
    """Returns a {identifiant_unique: est_parent} map for the given acteurs."""
    from qfdmo.models import VueActeur

    return dict(
        VueActeur.objects.filter(identifiant_unique__in=identifiants).values_list(
            "identifiant_unique", "est_parent"
        )
    )


def _filter_acteurs_a_mettre_a_jour(df: pd.DataFrame) -> pd.DataFrame:
    """Exclut les acteurs dont le couple SIREN/SIRET est déjà à jour."""
    return df[
        ~(
            (df[COLS.SIREN_ACTUEL] == df[COLS.SIREN_SUCCESSEUR])
            & (df[COLS.SIRET_ACTUEL] == df[COLS.SIRET_SUCCESSEUR])
        )
    ]


def enrich_lien_succession_to_suggestion_groupes(
    df: pd.DataFrame,
    cohort: str,
    suggest_action: str,
    identifiant_action: str,
    dry_run: bool = True,
) -> bool:
    """Write 1 SuggestionGroupe per replacement couple and 1
    SuggestionUnitaire per acteur, suggesting SIREN and SIRET."""
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

    df = _filter_acteurs_a_mettre_a_jour(df)
    if df.empty:
        logger.info("Aucun acteur à mettre à jour, rien à suggérer")
        return False

    identifiants = list(df[COLS.IDENTIFIANT_UNIQUE].unique())
    est_parent_map = _est_parent_par_acteur(identifiants)
    df = df[df[COLS.IDENTIFIANT_UNIQUE].isin(est_parent_map.keys())]
    if df.empty:
        logger.info("Aucun acteur visible correspondant, rien à suggérer")
        return False

    nb_groupes = df.groupby(GROUP_KEYS, dropna=False).ngroups
    nb_acteurs = len(df)
    metadata = {
        f"{cohort}: # couples source -> cible": nb_groupes,
        f"{cohort}: # Acteurs": nb_acteurs,
    }
    logger.info(log.banner_string(f"🏁 Cohorte {cohort}"))
    logger.info(f"{metadata=}")

    if dry_run:
        logger.info("✋ Dry run: suggestions pas écrites en base")
        return False

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

    for group_values, group_df in df.groupby(GROUP_KEYS, dropna=False):
        siren_actuel, siret_actuel, siren_successeur, siret_successeur = group_values
        with transaction.atomic():
            suggestion_groupe = SuggestionGroupe.objects.create(
                suggestion_cohorte=cohorte,
                statut=SuggestionStatut.AVALIDER,
                contexte={
                    "siren_actuel": siren_actuel,
                    "siret_actuel": siret_actuel,
                    "siren_successeur": siren_successeur,
                    "siret_successeur": siret_successeur,
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
                    champs=SUGGEST_FIELDS,
                    valeurs=[str(row[col]) for col in SUGGEST_VALUES],
                )

    return True


def enrich_lien_succession_suggest(
    dbt_model_name: str,
    cohort: str,
    suggest_action: str,
    identifiant_action: str,
    dry_run: bool = True,
) -> bool:
    """Reads a DBT model and generates grouped suggestions for it."""
    df = enrich_dbt_model_read(dbt_model_name)

    if df.empty:
        logger.info(f"0 donnée pour {dbt_model_name=}")
        return False

    return enrich_lien_succession_to_suggestion_groupes(
        df=df,
        cohort=cohort,
        suggest_action=suggest_action,
        identifiant_action=identifiant_action,
        dry_run=dry_run,
    )
