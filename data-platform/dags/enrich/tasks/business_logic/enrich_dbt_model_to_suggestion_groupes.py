"""Generate SuggestionGroupe/SuggestionUnitaire for the dbt based enrich DAGs
(acteurs closed, RGPD, villes & code postal).

The changes are prepared with the same functions as the legacy suggestions
(see enrich_dbt_model_to_suggestions) and then written as:
- villes & code postal: 1 SuggestionGroupe per (current value -> suggested value)
  and 1 SuggestionUnitaire per acteur, to validate identical corrections at once
- closed & RGPD: 1 SuggestionGroupe per acteur

In all cases, 1 SuggestionUnitaire per field (except latitude/longitude grouped),
like the source suggestions.
"""

import json
import logging

import pandas as pd
from enrich.config.cohorts import COHORTS
from enrich.config.columns import COLS
from enrich.tasks.business_logic.enrich_dbt_model_to_suggestions import (
    COHORTS_TO_PREPARE_CHANGES,
    cohort_to_suggestion_action,
)
from enrich.tasks.business_logic.enrich_siret_siren_suggest import (
    _est_parent_par_acteur,
)
from utils import logging_utils as log

logger = logging.getLogger(__name__)

MODELE_ACTEUR = "Acteur"
MODELE_REVISION_ACTEUR = "RevisionActeur"
MODELE_PARENT_REVISION_ACTEUR = "ParentRevisionActeur"

# Cohorts grouped by (current value -> suggested value): (champ, current, suggested)
COHORTS_GROUPED_BY_VALUE = {
    COHORTS.VILLES_TYPO: ("ville", COLS.ACTEUR_VILLE, COLS.SUGGEST_VILLE),
    COHORTS.VILLES_NEW: ("ville", COLS.ACTEUR_VILLE, COLS.SUGGEST_VILLE),
    COHORTS.ACTEUR_CP_TYPO: (
        "code_postal",
        COLS.CODE_POSTAL,
        COLS.SUGGEST_CODE_POSTAL,
    ),
    COHORTS.REVISION_ACTEUR_CP_TYPO: (
        "code_postal",
        COLS.CODE_POSTAL,
        COLS.SUGGEST_CODE_POSTAL,
    ),
}


def _unitaire(modele: str, identifiant_unique: str, data: dict) -> dict:
    return {
        "modele": modele,
        "identifiant_unique": identifiant_unique,
        "champs": list(data.keys()),
        "valeurs": [str(valeur) for valeur in data.values()],
    }


def _unitaires_par_champ(modele: str, identifiant_unique: str, data: dict) -> list:
    """1 unitaire per field, except grouped fields (latitude, longitude), the
    same way as the source suggestions"""
    from data.models.suggestions.source import SuggestionSourceModel

    champs_groupes = [
        champs
        for champs in SuggestionSourceModel.get_ordered_fields()
        if all(champ in data for champ in champs)
    ]
    champs_traites = {champ for champs in champs_groupes for champ in champs}
    champs_groupes += [(champ,) for champ in data if champ not in champs_traites]
    return [
        _unitaire(modele, identifiant_unique, {champ: data[champ] for champ in champs})
        for champs in champs_groupes
    ]


def _modele_revision(identifiant_unique: str, est_parent_map: dict) -> str:
    if est_parent_map.get(identifiant_unique, False):
        return MODELE_PARENT_REVISION_ACTEUR
    return MODELE_REVISION_ACTEUR


def _commentaires_ajouter(existing: str | None, added: str) -> str:
    """Same logic as Acteur.commentaires_ajouter, without saving"""
    if existing is None or existing.strip() == "":
        return json.dumps([{"message": added}])
    try:
        existing_data = json.loads(existing)
        if not isinstance(existing_data, list):
            raise NotImplementedError("Cas de commentaires JSON non-liste pas prévu")
    except (json.JSONDecodeError, ValueError):
        existing_data = [{"message": existing}]
    existing_data.append({"message": added})
    return json.dumps(existing_data)


def _unitaires_rgpd(identifiant_unique: str, data: dict) -> list[dict]:
    """RGPD overwrites the Acteur and its RevisionActeur if it exists, without
    creating a revision (same intent as ChangeActeurRgpdAnonymize), with 1
    unitaire per field"""
    from qfdmo.models import Acteur, RevisionActeur

    commentaire = data["commentaires"]
    instances: list[tuple[str, Acteur | RevisionActeur]] = [
        (MODELE_ACTEUR, Acteur.objects.get(pk=identifiant_unique))
    ]
    revision = RevisionActeur.objects.filter(pk=identifiant_unique).first()
    if revision:
        instances.append((MODELE_REVISION_ACTEUR, revision))

    return [
        unitaire
        for modele, instance in instances
        for unitaire in _unitaires_par_champ(
            modele,
            identifiant_unique,
            {
                **data,
                "commentaires": _commentaires_ajouter(
                    instance.commentaires, commentaire
                ),
            },
        )
    ]


def _unitaires_prepare(
    cohort: str, identifiant_unique: str, data: dict, est_parent_map: dict
) -> list[dict]:
    if cohort == COHORTS.RGPD:
        return _unitaires_rgpd(identifiant_unique, data)
    if cohort == COHORTS.ACTEUR_CP_TYPO:
        return _unitaires_par_champ(MODELE_ACTEUR, identifiant_unique, data)
    modele = _modele_revision(identifiant_unique, est_parent_map)
    return _unitaires_par_champ(modele, identifiant_unique, data)


def _groupe_acteurs_fks(identifiant_unique: str) -> dict:
    """Acteur, RevisionActeur and parent of a per acteur SuggestionGroupe, the
    same way as the source suggestions, so the changes can be reported on the
    parent from the admin"""
    from qfdmo.models import Acteur, RevisionActeur

    revision = RevisionActeur.objects.filter(pk=identifiant_unique).first()
    if Acteur.objects.filter(pk=identifiant_unique).exists():
        return {
            "acteur_id": identifiant_unique,
            "revision_acteur_id": revision.pk if revision else None,
            "parent_revision_acteur_id": revision.parent_id if revision else None,
        }
    # The acteur is a parent: it only exists as a RevisionActeur
    return {"parent_revision_acteur_id": revision.pk if revision else None}


def suggestion_groupes_prepare(
    df: pd.DataFrame, cohort: str, est_parent_map: dict
) -> list[dict]:
    """Prepare the groupes without writing them:
    [{"contexte": {...}, "fks": {acteur_id, revision_acteur_id,
    parent_revision_acteur_id}, "unitaires": [{modele, identifiant_unique, champs,
    valeurs}]}]"""
    change_preparation_function = COHORTS_TO_PREPARE_CHANGES[cohort]
    grouped_by = COHORTS_GROUPED_BY_VALUE.get(cohort)

    groupes: dict[tuple, dict] = {}
    for _, row in df.iterrows():
        row = dict(row)
        identifiant_unique = row[COLS.ACTEUR_ID]
        try:
            changes, contexte = change_preparation_function(row)
            data = changes[0]["model_params"]["data"]

            if grouped_by:
                champ, col_actuelle, col_suggeree = grouped_by
                actuelle, suggeree = row[col_actuelle], row[col_suggeree]
                if pd.isna(suggeree) or suggeree == "" or suggeree == actuelle:
                    logger.info(f"{identifiant_unique}: rien à suggérer pour {champ}")
                    continue
                key = (actuelle, suggeree)
                fks = {}
                contexte = {
                    f"{champ} actuel(le)": actuelle,
                    f"{champ} proposé(e)": suggeree,
                }
            else:
                key = (identifiant_unique,)
                fks = _groupe_acteurs_fks(identifiant_unique)
                contexte = {"identifiant_unique": identifiant_unique, **contexte}

            unitaires = _unitaires_prepare(
                cohort, identifiant_unique, data, est_parent_map
            )

        # We tolerate some errors
        except Exception as e:
            log.preview("🔴 Suggestion problématique", row)
            logger.error(f"Erreur de préparation des changements: {e}")
            continue

        groupe = groupes.setdefault(
            key, {"contexte": contexte, "fks": fks, "unitaires": []}
        )
        groupe["unitaires"].extend(unitaires)

    for groupe in groupes.values():
        if grouped_by:
            groupe["contexte"]["# acteurs"] = len(groupe["unitaires"])
    return list(groupes.values())


def enrich_dbt_model_to_suggestion_groupes(
    df: pd.DataFrame,
    cohort: str,
    identifiant_action: str,
    dry_run: bool = True,
) -> bool:
    from utils.django import django_setup_full

    django_setup_full()

    from data.models.suggestion import (
        SuggestionCohorte,
        SuggestionGroupe,
        SuggestionStatut,
        SuggestionUnitaire,
    )
    from django.db import transaction

    # Validation
    if df is None or df.empty:
        raise ValueError("df vide: on devrait pas être ici")

    cohorts = list(df[COLS.SUGGEST_COHORT].unique())
    if len(cohorts) != 1 or cohorts[0] != cohort:
        msg = f"Problème cohorte: obtenu {cohorts=} vs. attendu {cohort=}"
        raise ValueError(msg)

    est_parent_map = _est_parent_par_acteur(list(df[COLS.ACTEUR_ID].unique()))
    groupes = suggestion_groupes_prepare(df, cohort, est_parent_map)

    # we need some working suggestions, can't have it all fail
    if not groupes:
        raise ValueError("Aucune suggestion à écrire, pas normal")

    metadata = {
        f"{cohort}: # Groupes": len(groupes),
        f"{cohort}: # Suggestions unitaires": sum(
            len(groupe["unitaires"]) for groupe in groupes
        ),
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
        type_action=cohort_to_suggestion_action(cohort),
        statut=SuggestionStatut.AVALIDER,
        metadata=metadata,
    )
    cohorte.save()

    for groupe in groupes:
        with transaction.atomic():
            suggestion_groupe = SuggestionGroupe.objects.create(
                suggestion_cohorte=cohorte,
                statut=SuggestionStatut.AVALIDER,
                contexte=groupe["contexte"],
                **groupe["fks"],
            )
            for unitaire in groupe["unitaires"]:
                modele = unitaire["modele"]
                identifiant_unique = unitaire["identifiant_unique"]
                SuggestionUnitaire.objects.create(
                    suggestion_groupe=suggestion_groupe,
                    statut=SuggestionStatut.AVALIDER,
                    acteur_id=(identifiant_unique if modele == MODELE_ACTEUR else None),
                    revision_acteur_id=(
                        identifiant_unique if modele == MODELE_REVISION_ACTEUR else None
                    ),
                    parent_revision_acteur_id=(
                        identifiant_unique
                        if modele == MODELE_PARENT_REVISION_ACTEUR
                        else None
                    ),
                    suggestion_modele=modele,
                    raison=cohort,
                    champs=unitaire["champs"],
                    valeurs=unitaire["valeurs"],
                )

    return True
