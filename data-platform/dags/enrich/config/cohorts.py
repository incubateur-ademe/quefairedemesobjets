"""Cohorts for enrich DAGs"""

from dataclasses import dataclass


@dataclass(frozen=True)
class COHORTS:
    CLOSED_NOT_REPLACED_UNITE = "🚪 Acteurs Fermés: 🔴 non remplacés - unité fermée"
    CLOSED_NOT_REPLACED_ETABLISSEMENT = (
        "🚪 Acteurs Fermés: 🔴 non remplacés - établissement fermé"
    )
    CLOSED_REP_OTHER_SIREN = (
        "🚪 Acteurs Fermés: 🟡 remplacés par SIRET d'un autre SIREN"
    )
    CLOSED_REP_SAME_SIREN = "🚪 Acteurs Fermés: 🟢 remplacés par SIRET du même SIREN"
    RGPD = "Anonymisation RGPD"
    VILLES_TYPO = "🌆 Changement de ville: 🟢 variation d'ortographe"
    VILLES_NEW = "🌆 Changement de ville: 🟡 ancienne -> nouvelle"
    ACTEUR_CP_TYPO = (
        "🌆 Changement de code postal pour les acteurs: 🟢 respect du formalisme"
    )
    REVISION_ACTEUR_CP_TYPO = (
        "🌆 Changement de code postal pour les revisions: 🟢 respect du formalisme"
    )
