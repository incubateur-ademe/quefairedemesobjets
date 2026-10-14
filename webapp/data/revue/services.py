"""Writes of the review screen.

Each write locks the groupe (`select_for_update`), checks that it did not change
since the reviewer loaded it (`modifie_le`, otherwise 409 with its current state),
checks the capabilities of the review policy, touches the groupe and recomputes
the statut of the cohorte. Validating only sets the statut to ATRAITER: the
suggestions are applied later by the existing tasks.
"""

from collections.abc import Callable
from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from data.models.suggestion import (
    SuggestionGroupe,
    SuggestionStatut,
    SuggestionUnitaire,
)
from data.revue.errors import RevueApiError
from data.revue.lignes import ACTEUR, groupes_queryset, serialize_groupe
from data.revue.policies import PARENT, REVISION, ReviewPolicy, get_policy
from data.views import update_suggestion_groupe

AVALIDER = SuggestionStatut.AVALIDER
ATRAITER = SuggestionStatut.ATRAITER
REJETEE = SuggestionStatut.REJETEE


def _same_instant(a: datetime, b: datetime) -> bool:
    """`modifie_le` is sent to the client with a millisecond precision (JSON)."""
    return abs((a - b).total_seconds()) < 0.001


def _conflict(groupe: SuggestionGroupe, policy: ReviewPolicy, detail: str):
    return RevueApiError(
        409, "conflict", detail, current=serialize_groupe(groupe, policy)
    )


def write_groupe(
    groupe_id: int,
    expected_modifie_le: datetime | None,
    write: Callable[[SuggestionGroupe, ReviewPolicy, dict], None],
) -> dict:
    """Runs `write(groupe, policy, lignes)` on the locked groupe and returns the
    serialized groupe after the write."""
    with transaction.atomic():
        groupe = (
            SuggestionGroupe.objects.select_for_update(of=("self",))
            .select_related("suggestion_cohorte")
            .filter(id=groupe_id)
            .first()
        )
        if groupe is None:
            raise RevueApiError(404, "not_found", "Groupe introuvable")
        policy = get_policy(groupe.suggestion_cohorte.type_action)
        groupe = groupes_queryset().get(id=groupe_id)
        if expected_modifie_le is not None and not _same_instant(
            groupe.modifie_le, expected_modifie_le
        ):
            raise _conflict(
                groupe, policy, "Ce groupe a été modifié entre-temps, il a été rechargé"
            )
        current = serialize_groupe(groupe, policy)
        lignes = {tuple(ligne["champs"]): ligne for ligne in current["lignes"]}
        write(groupe, policy, {"groupe": current, "lignes": lignes})
        SuggestionGroupe.objects.filter(id=groupe_id).update(modifie_le=timezone.now())
        groupe.suggestion_cohorte.recompute_cohorte_statut()
    return serialize_groupe(groupes_queryset().get(id=groupe_id), policy)


def _refuse(groupe, policy, detail: str):
    raise _conflict(groupe, policy, detail)


def _lignes(state: dict, champs_list: list[list[str]], groupe, policy) -> list[dict]:
    lignes = []
    for champs in champs_list:
        ligne = state["lignes"].get(tuple(champs))
        if ligne is None:
            raise RevueApiError(
                404, "not_found", f"Ligne « {', '.join(champs)} » introuvable"
            )
        lignes.append(ligne)
    return lignes


# --- Decisions ---


def decide_groupe(groupe_id, action: str, user, expected_modifie_le) -> dict:
    def write(groupe, policy, state):
        capacites = state["groupe"]["capacites"]
        if action == "validate":
            if not capacites["valider"]:
                _refuse(groupe, policy, "Ce groupe n'est plus à valider")
            groupe.suggestion_cohorte.set_groupes_statut([groupe.id], ATRAITER, user)
        elif action == "reject":
            if not capacites["refuser"]:
                _refuse(groupe, policy, "Ce groupe ne peut plus être refusé")
            groupe.suggestion_cohorte.set_groupes_statut([groupe.id], REJETEE, user)
        elif action == "resubmit":
            if not capacites["remettre_a_valider"]:
                _refuse(groupe, policy, "Ce groupe ne peut pas être remis à valider")
            groupe.suggestion_cohorte.set_groupes_statut([groupe.id], AVALIDER)

    return write_groupe(groupe_id, expected_modifie_le, write)


def decide_lignes(
    groupe_id, champs_list: list[list[str]], action: str, user, expected_modifie_le
) -> dict:
    def write(groupe, policy, state):
        lignes = _lignes(state, champs_list, groupe, policy)
        if action == "validate":
            if not all(ligne["capacites"]["valider"] for ligne in lignes):
                _refuse(groupe, policy, "Cette ligne n'est plus à valider")
            groupe.set_lignes_statut(champs_list, ATRAITER, user)
            # The groupe is validated with its last ligne
            if not groupe.suggestion_unitaires.exclude(statut=ATRAITER).exists():
                groupe.suggestion_cohorte.set_groupes_statut(
                    [groupe.id], ATRAITER, user
                )
        elif action == "resubmit":
            if groupe.statut == REJETEE:
                # Refusal is a decision on the whole groupe: reopen it
                groupe.suggestion_cohorte.set_groupes_statut([groupe.id], AVALIDER)
                return
            if not all(ligne["capacites"]["remettre_a_valider"] for ligne in lignes):
                _refuse(groupe, policy, "Cette ligne ne peut pas être remise à valider")
            groupe.set_lignes_statut(champs_list, AVALIDER)
            if groupe.statut == ATRAITER:
                SuggestionGroupe.objects.filter(id=groupe.id).update(
                    statut=AVALIDER, decision_par=None, decision_le=None
                )

    return write_groupe(groupe_id, expected_modifie_le, write)


# --- Corrections ---

CAPACITY = {REVISION: "correction", PARENT: "parent"}


def _target_id(groupe: SuggestionGroupe, modele: str) -> str | None:
    if modele == PARENT:
        return groupe.parent_revision_acteur_id
    return (
        groupe.revision_acteur_id
        or groupe.acteur_id
        or groupe.get_identifiant_unique_from_suggestion_unitaires()
    )


def _validation_errors(errors: dict) -> dict[str, list[str]]:
    result = {}
    for field, messages in errors.items():
        if not isinstance(messages, list | tuple):
            messages = [messages]
        flat = []
        for message in messages:
            if isinstance(message, ValidationError):
                flat += message.messages
            else:
                flat.append(str(message))
        result[field] = flat
    return result


def upsert_proposition(
    groupe_id, modele: str, champs: list[str], valeurs: dict, expected_modifie_le
) -> dict:
    def write(groupe, policy, state):
        (ligne,) = _lignes(state, [champs], groupe, policy)
        if not ligne["capacites"][f"corriger_{CAPACITY[modele]}"]:
            _refuse(groupe, policy, "Cette ligne n'est pas corrigeable")
        unknown = set(valeurs) - set(champs)
        if unknown:
            raise RevueApiError(
                422, "invalid", f"Champs hors de la ligne : {sorted(unknown)}"
            )
        ok, errors = update_suggestion_groupe(
            groupe,
            modele,
            valeurs,
            [tuple(c) for c in state["lignes"]],
            identifiant_unique=_target_id(groupe, modele) or "",
        )
        if not ok:
            raise RevueApiError(
                422,
                "validation",
                "Valeur refusée",
                errors=_validation_errors(errors or {}),
            )

    return write_groupe(groupe_id, expected_modifie_le, write)


def delete_proposition(
    groupe_id, modele: str, champs: list[str], expected_modifie_le
) -> dict:
    def write(groupe, policy, state):
        (ligne,) = _lignes(state, [champs], groupe, policy)
        if not ligne["capacites"][f"supprimer_{CAPACITY[modele]}"]:
            _refuse(groupe, policy, "Cette proposition ne peut pas être supprimée")
        SuggestionUnitaire.objects.filter(
            suggestion_groupe=groupe, suggestion_modele=modele, champs=champs
        ).delete()

    return write_groupe(groupe_id, expected_modifie_le, write)


def report_lignes(
    groupe: SuggestionGroupe,
    modele: str,
    lignes: list[dict],
) -> int:
    """Copies the suggestion of the source (SU Acteur) to the target SU of each
    reportable ligne, creating it if needed. Does not validate the lignes."""
    target_field = (
        "parent_revision_acteur_id" if modele == PARENT else ("revision_acteur_id")
    )
    target_id = _target_id(groupe, modele)
    sus = {
        (su.suggestion_modele, tuple(su.champs)): su
        for su in groupe.suggestion_unitaires.all()
    }
    count = 0
    for ligne in lignes:
        if not ligne["capacites"][f"reporter_{CAPACITY[modele]}"] or not target_id:
            continue
        champs = tuple(ligne["champs"])
        source = sus[(ACTEUR, champs)]
        target = sus.get((modele, champs))
        if target is None:
            target = SuggestionUnitaire(
                suggestion_groupe=groupe,
                suggestion_modele=modele,
                champs=list(champs),
                ordre=source.ordre,
                statut=source.statut,
                **{target_field: target_id},
            )
        target.valeurs = list(source.valeurs)
        target.save()
        count += 1
    return count


def report(
    groupe_id, cible: str, champs_list: list[list[str]] | None, expected_modifie_le
) -> dict:
    modele = REVISION if cible == "correction" else PARENT

    def write(groupe, policy, state):
        lignes = (
            list(state["lignes"].values())
            if champs_list is None
            else _lignes(state, champs_list, groupe, policy)
        )
        if not report_lignes(groupe, modele, lignes):
            _refuse(groupe, policy, "Aucune ligne reportable")

    return write_groupe(groupe_id, expected_modifie_le, write)
