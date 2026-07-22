"""Generate SuggestionGroupe/SuggestionUnitaire for lien succession enrichments.

One SuggestionGroupe is written per corrected acteur, with one SuggestionUnitaire
per changed field (SIREN and/or SIRET).
"""

import logging

import pandas as pd
from enrich.config.columns import COLS
from enrich.tasks.business_logic.enrich_dbt_model_read import enrich_dbt_model_read
from utils import logging_utils as log
from utils.django import django_setup_full

logger = logging.getLogger(__name__)

SUGGEST_FIELD_UPDATES = [
    (COLS.SIREN, COLS.SIREN_ACTUEL, COLS.SIREN_SUCCESSEUR),
    (COLS.SIRET, COLS.SIRET_ACTUEL, COLS.SIRET_SUCCESSEUR),
]


def _est_parent_par_acteur(identifiants: list[str]) -> dict[str, bool]:
    """Returns a {identifiant_unique: est_parent} map for the given acteurs."""
    from qfdmo.models import VueActeur

    return dict(
        VueActeur.objects.filter(identifiant_unique__in=identifiants).values_list(
            "identifiant_unique", "est_parent"
        )
    )


def _filter_acteurs_a_mettre_a_jour(df: pd.DataFrame) -> pd.DataFrame:
    """Exclut les acteurs dont SIREN et SIRET sont déjà à jour."""
    return df[
        (df[COLS.SIREN_ACTUEL] != df[COLS.SIREN_SUCCESSEUR])
        | (df[COLS.SIRET_ACTUEL] != df[COLS.SIRET_SUCCESSEUR])
    ]


def _champs_a_suggerer(row: pd.Series) -> list[tuple[str, str]]:
    """Retourne les champs à suggérer dont la valeur diffère de l'actuelle."""
    return [
        (champ, str(row[valeur_successeur]))
        for champ, valeur_actuelle, valeur_successeur in SUGGEST_FIELD_UPDATES
        if row[valeur_actuelle] != row[valeur_successeur]
    ]


def enrich_lien_succession_to_suggestion_groupes(
    df: pd.DataFrame,
    cohort: str,
    suggest_action: str,
    identifiant_action: str,
    dry_run: bool = True,
) -> bool:
    """Write 1 SuggestionGroupe per acteur and 1 SuggestionUnitaire per changed
    field (SIREN and/or SIRET)."""
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

    nb_acteurs = len(df)
    metadata = {
        f"{cohort}: # suggestions": nb_acteurs,
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

    for _, row in df.iterrows():
        identifiant_unique = row[COLS.IDENTIFIANT_UNIQUE]
        est_parent = est_parent_map.get(identifiant_unique, False)
        parent_revision = None
        suggestion_modele = "RevisionActeur"
        if est_parent:
            parent_revision = RevisionActeur.objects.get(
                identifiant_unique=identifiant_unique
            )
            suggestion_modele = "ParentRevisionActeur"

        champs_a_suggerer = _champs_a_suggerer(row)
        if not champs_a_suggerer:
            continue

        with transaction.atomic():
            suggestion_groupe = SuggestionGroupe.objects.create(
                suggestion_cohorte=cohorte,
                statut=SuggestionStatut.AVALIDER,
                contexte={
                    "siren_actuel": row[COLS.SIREN_ACTUEL],
                    "siret_actuel": row[COLS.SIRET_ACTUEL],
                    "siren_successeur": row[COLS.SIREN_SUCCESSEUR],
                    "siret_successeur": row[COLS.SIRET_SUCCESSEUR],
                },
            )
            for champ, valeur in champs_a_suggerer:
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
                    champs=[champ],
                    valeurs=[valeur],
                )

    return True


def enrich_lien_succession_suggest(
    dbt_model_name: str,
    cohort: str,
    suggest_action: str,
    identifiant_action: str,
    dry_run: bool = True,
) -> bool:
    """Reads a DBT model and generates one suggestion per corrected acteur."""
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
