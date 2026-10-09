"""Statut writes of the review screen (data/revue) and of the apply tasks.

The Django admin keeps its own statut management: both live in parallel.

A SuggestionGroupe statut is always written together with the statut of its
SuggestionUnitaire, so that the « lignes de suggestion » (built from the
SuggestionUnitaire) stay consistent with their groupe.
"""

from collections.abc import Iterable

from data.models.suggestion import (
    SuggestionCohorte,
    SuggestionCohorteStatut,
    SuggestionGroupe,
    SuggestionStatut,
    SuggestionUnitaire,
)
from django.db import transaction
from django.utils import timezone

HUMAN_DECISION_STATUTS = [SuggestionStatut.ATRAITER, SuggestionStatut.REJETEE]
PROCESSING_STATUTS = [
    SuggestionStatut.ENCOURS,
    SuggestionStatut.SUCCES,
    SuggestionStatut.ERREUR,
]
FINISHED_STATUTS = {
    SuggestionStatut.SUCCES,
    SuggestionStatut.ERREUR,
    SuggestionStatut.REJETEE,
}


def _statut_fields(statut: str, user=None) -> dict:
    """Fields to update with the statut: a human decision is traced, putting back
    to AVALIDER clears the trace, processing statuts keep it untouched."""
    fields = {"statut": statut, "modifie_le": timezone.now()}
    if statut in HUMAN_DECISION_STATUTS:
        fields |= {"decision_par": user, "decision_le": timezone.now()}
    elif statut == SuggestionStatut.AVALIDER:
        fields |= {"decision_par": None, "decision_le": None}
    return fields


def set_groupes_statut(groupe_ids: Iterable[int], statut: str, user=None) -> int:
    """Set the statut of the groupes and of all their SuggestionUnitaire.
    Returns the number of updated groupes."""
    groupe_ids = list(groupe_ids)
    fields = _statut_fields(statut, user)
    with transaction.atomic():
        SuggestionUnitaire.objects.filter(suggestion_groupe_id__in=groupe_ids).update(
            **fields
        )
        return SuggestionGroupe.objects.filter(id__in=groupe_ids).update(**fields)


def set_lignes_statut(
    groupe: SuggestionGroupe,
    champs_list: Iterable[list[str]],
    statut: str,
    user=None,
) -> int:
    """Set the statut of the SuggestionUnitaire of the given lignes (a ligne is
    identified by its `champs` tuple, all suggestion_modele included).
    The groupe statut is left to the caller."""
    return SuggestionUnitaire.objects.filter(
        suggestion_groupe=groupe, champs__in=[list(c) for c in champs_list]
    ).update(**_statut_fields(statut, user))


def compute_cohorte_statut(groupe_statuts: set[str]) -> str | None:
    if not groupe_statuts:
        return None
    if SuggestionStatut.AVALIDER in groupe_statuts:
        return SuggestionCohorteStatut.AVALIDER
    if groupe_statuts <= FINISHED_STATUTS:
        return SuggestionCohorteStatut.SUCCES
    return SuggestionCohorteStatut.ENCOURS


def recompute_cohorte_statut(cohorte_ids: Iterable[int]) -> None:
    """Recompute the statut of the cohortes from the statut of their groupes.
    Cohortes without groupe (legacy Suggestion) are left untouched."""
    for cohorte in SuggestionCohorte.objects.prefetch_related(
        "suggestion_groupes"
    ).filter(id__in=list(cohorte_ids)):
        statut = compute_cohorte_statut(
            set(cohorte.suggestion_groupes.values_list("statut", flat=True).distinct())
        )
        if statut and statut != cohorte.statut:
            cohorte.statut = statut
            cohorte.save(update_fields=["statut", "modifie_le"])
