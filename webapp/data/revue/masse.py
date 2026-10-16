"""Mass actions of the review screen, on a selection like in the Django admin:
- `ids`: the elements checked on the page (groupe ids, or ligne keys);
- `filtre`: every element matching the filter (same filter, tuples and « afficher »
  as the list, re-applied by the server), except the `exclus`.

Decisions are bulk SQL updates (fast at any size). Reports copy suggestions
groupe by groupe: synchronous up to SUGGESTION_TASK_ASYNC_THRESHOLD groupes,
otherwise run by a django-tasks task followed by the client.
"""

from dataclasses import dataclass

from django.db import transaction
from django.db.models import Exists, OuterRef, Q, QuerySet
from django.utils import timezone
from django_tasks import TaskResultStatus, task

from data.models.suggestion import (
    SuggestionCohorte,
    SuggestionGroupe,
    SuggestionStatut,
    SuggestionUnitaire,
)
from data.revue.errors import RevueApiError
from data.revue.filters import parse_filter
from data.revue.lignes import (
    ACTEUR,
    NOT_EDITABLE,
    NOT_REPORTABLE,
    groupes_queryset,
    parse_ligne_key,
    serialize_groupe,
)
from data.revue.policies import PARENT, REVISION, get_policy
from data.revue.revue import (
    _ligne_key_expression,
    filtered_groupes,
    filtered_ligne_rows,
    parse_tuples,
)

SUGGESTION_TASK_ASYNC_THRESHOLD = 1000
BATCH = 5000

AVALIDER = SuggestionStatut.AVALIDER
ATRAITER = SuggestionStatut.ATRAITER
REJETEE = SuggestionStatut.REJETEE
REOPENABLE = [ATRAITER, REJETEE]

ACTIONS = ["validate", "reject", "resubmit", "report_correction", "report_parent"]
REPORT_TARGETS = {"report_correction": REVISION, "report_parent": PARENT}


@dataclass
class Selection:
    cohorte: SuggestionCohorte
    vue: str
    # Groupes view: the selected groupes. Lignes view: the SU rows of the
    # selected lignes (every SU of a selected ligne).
    groupes: QuerySet[SuggestionGroupe] | None = None
    rows: QuerySet[SuggestionUnitaire] | None = None


def resolve(cohorte: SuggestionCohorte, payload: dict) -> Selection:
    vue = payload["vue"]
    selection = payload["selection"]
    if selection["mode"] == "ids":
        ids = selection["ids"]
        if vue == "groupes":
            groupes = cohorte.suggestion_groupes.filter(id__in=[int(i) for i in ids])
            return Selection(cohorte, vue, groupes=groupes)
        q = Q(pk__in=[])
        for key in ids:
            groupe_id, champs = parse_ligne_key(str(key))
            q |= Q(suggestion_groupe_id=groupe_id, champs=champs)
        rows = SuggestionUnitaire.objects.filter(
            q, suggestion_groupe__suggestion_cohorte=cohorte
        )
        return Selection(cohorte, vue, rows=rows)

    filtre = parse_filter(selection.get("filtre"))
    tuples = parse_tuples(selection.get("tuples") or [])
    afficher = selection.get("afficher")
    exclus = selection.get("exclus") or []
    if vue == "groupes":
        groupes = filtered_groupes(cohorte, filtre, tuples, afficher).exclude(
            id__in=[int(i) for i in exclus]
        )
        return Selection(cohorte, vue, groupes=groupes)
    rows = filtered_ligne_rows(cohorte, filtre, tuples, afficher)
    if exclus:
        rows = rows.alias(_cle=_ligne_key_expression()).exclude(
            _cle__in=[str(k) for k in exclus]
        )
    # Plain queryset on the ids: updatable, and reusable in subqueries
    rows = SuggestionUnitaire.objects.filter(pk__in=rows.values("pk"))
    return Selection(cohorte, vue, rows=rows)


# --- Querysets of what each action really concerns ---


def _all_rows(selection: Selection) -> QuerySet[SuggestionUnitaire]:
    """SU of the selected elements (all the SU of a selected groupe)."""
    if selection.vue == "groupes":
        return SuggestionUnitaire.objects.filter(
            suggestion_groupe__in=selection.groupes.values("id")
        )
    return selection.rows


def _reportable_acteur_rows(selection: Selection, modele: str):
    """SU Acteur of the lignes that may be reported to `modele`: groupe and ligne
    to validate, no field forbidden on the target."""
    policy = get_policy(selection.cohorte.type_action)
    if modele not in policy.editable_models:
        return SuggestionUnitaire.objects.none()
    rows = _all_rows(selection).filter(
        suggestion_modele=ACTEUR,
        statut=AVALIDER,
        suggestion_groupe__statut=AVALIDER,
    )
    forbidden = sorted(NOT_REPORTABLE[modele] | NOT_EDITABLE)
    rows = rows.exclude(champs__overlap=forbidden)
    if modele == PARENT:
        rows = rows.filter(suggestion_groupe__parent_revision_acteur__isnull=False)
    return rows


def _count_lignes(rows: QuerySet[SuggestionUnitaire]) -> int:
    return rows.order_by().values("suggestion_groupe_id", "champs").distinct().count()


def preview(selection: Selection) -> dict[str, int]:
    """Number of elements (groupes or lignes) each action would really change."""
    policy = get_policy(selection.cohorte.type_action)
    if selection.vue == "groupes":
        groupes = selection.groupes
        counts = {
            "validate": groupes.filter(statut=AVALIDER).count(),
            "reject": (
                groupes.filter(statut=AVALIDER).count()
                if policy.can_reject_group
                else 0
            ),
            "resubmit": _groupes_to_resubmit(groupes).count(),
        }
        for action, modele in REPORT_TARGETS.items():
            counts[action] = (
                _reportable_acteur_rows(selection, modele)
                .values("suggestion_groupe_id")
                .distinct()
                .count()
            )
        return counts

    rows = selection.rows
    return {
        "validate": _count_lignes(_lignes_to_validate(rows)),
        "reject": 0,
        "resubmit": _count_lignes(_lignes_to_resubmit(rows)),
        **{
            action: _count_lignes(_reportable_acteur_rows(selection, modele))
            for action, modele in REPORT_TARGETS.items()
        },
    }


def _lignes_to_validate(rows):
    """Rows of the lignes to validate: groupe to validate, not all SU validated."""
    not_validated = SuggestionUnitaire.objects.filter(
        suggestion_groupe_id=OuterRef("suggestion_groupe_id"),
        champs=OuterRef("champs"),
    ).exclude(statut=ATRAITER)
    return rows.filter(suggestion_groupe__statut=AVALIDER).filter(Exists(not_validated))


def _lignes_to_resubmit(rows):
    """Rows of validated lignes (groupe not processed yet), and of lignes of
    refused groupes (which reopen their whole groupe)."""
    open_not_validated = SuggestionUnitaire.objects.filter(
        suggestion_groupe_id=OuterRef("suggestion_groupe_id"),
        champs=OuterRef("champs"),
    ).exclude(statut=ATRAITER)
    validated = rows.filter(suggestion_groupe__statut=ATRAITER) | rows.filter(
        suggestion_groupe__statut=AVALIDER
    ).exclude(Exists(open_not_validated))
    return validated | rows.filter(suggestion_groupe__statut=REJETEE)


# --- Execution ---


def _batches(ids: list[int]):
    for start in range(0, len(ids), BATCH):
        yield ids[start : start + BATCH]


def run(selection: Selection, action: str, user) -> dict:
    if action not in ACTIONS:
        raise RevueApiError(422, "invalid", f"Action inconnue : « {action} »")
    if action == "reject" and selection.vue == "lignes":
        raise RevueApiError(
            422, "invalid", "Une ligne ne peut pas être refusée : refuser le groupe"
        )
    policy = get_policy(selection.cohorte.type_action)
    if action == "reject" and not policy.can_reject_group:
        raise RevueApiError(422, "invalid", "Refus impossible pour ce type")
    total = preview(selection)[action]
    if action in REPORT_TARGETS:
        return _report(selection, REPORT_TARGETS[action], total)
    with transaction.atomic():
        if selection.vue == "groupes":
            affected = _decide_groupes(selection, action, user)
        else:
            affected = _decide_lignes(selection, action, user)
        selection.cohorte.recompute_cohorte_statut()
    return {"affected": affected, "skipped": max(total - affected, 0)}


def _groupes_to_resubmit(groupes: QuerySet[SuggestionGroupe]):
    """Decided groupes (validated or refused, not processed yet), and groupes to
    validate having validated lignes: all their lignes go back to validate."""
    with_validated_lignes = Exists(
        SuggestionUnitaire.objects.filter(
            suggestion_groupe_id=OuterRef("pk"), statut=ATRAITER
        )
    )
    return groupes.filter(
        Q(statut__in=REOPENABLE) | (Q(statut=AVALIDER) & Q(with_validated_lignes))
    )


def _decide_groupes(selection: Selection, action: str, user) -> int:
    if action == "resubmit":
        targets, target = _groupes_to_resubmit(selection.groupes), AVALIDER
    else:
        target = ATRAITER if action == "validate" else REJETEE
        targets = selection.groupes.filter(statut=AVALIDER)
    ids = list(
        SuggestionGroupe.objects.select_for_update()
        .filter(id__in=list(targets.values_list("id", flat=True)))
        .values_list("id", flat=True)
    )
    for batch in _batches(ids):
        selection.cohorte.set_groupes_statut(
            batch, target, user if target != AVALIDER else None
        )
    return len(ids)


def _decide_lignes(selection: Selection, action: str, user) -> int:
    now = timezone.now()
    rows = selection.rows
    if action == "validate":
        lignes = _lignes_to_validate(rows)
        affected = _count_lignes(lignes)
        groupe_ids = list(
            lignes.values_list("suggestion_groupe_id", flat=True).distinct()
        )
        SuggestionUnitaire.objects.filter(
            pk__in=list(lignes.values_list("pk", flat=True))
        ).update(statut=ATRAITER, decision_par=user, decision_le=now, modifie_le=now)
        # A groupe is validated with its last ligne
        complete = SuggestionGroupe.objects.filter(
            id__in=groupe_ids, statut=AVALIDER
        ).exclude(
            Exists(
                SuggestionUnitaire.objects.filter(
                    suggestion_groupe_id=OuterRef("pk")
                ).exclude(statut=ATRAITER)
            )
        )
        complete.update(
            statut=ATRAITER, decision_par=user, decision_le=now, modifie_le=now
        )
        SuggestionGroupe.objects.filter(id__in=groupe_ids).update(modifie_le=now)
        return affected

    # resubmit
    lignes = _lignes_to_resubmit(rows)
    affected = _count_lignes(lignes)
    # Refusal is a decision on the groupe: its lignes reopen the whole groupe
    refused = list(
        lignes.filter(suggestion_groupe__statut=REJETEE)
        .values_list("suggestion_groupe_id", flat=True)
        .distinct()
    )
    for batch in _batches(refused):
        selection.cohorte.set_groupes_statut(batch, AVALIDER)
    validated = lignes.exclude(suggestion_groupe__statut=REJETEE)
    groupe_ids = list(
        validated.values_list("suggestion_groupe_id", flat=True).distinct()
    )
    SuggestionUnitaire.objects.filter(
        pk__in=list(validated.values_list("pk", flat=True))
    ).update(statut=AVALIDER, decision_par=None, decision_le=None, modifie_le=now)
    SuggestionGroupe.objects.filter(id__in=groupe_ids, statut=ATRAITER).update(
        statut=AVALIDER, decision_par=None, decision_le=None
    )
    SuggestionGroupe.objects.filter(id__in=groupe_ids).update(modifie_le=now)
    return affected


# --- Reports ---


def _report_plan(selection: Selection, modele: str) -> dict[int, list[list[str]]]:
    """Lignes to report, by groupe."""
    plan: dict[int, list[list[str]]] = {}
    for groupe_id, champs in (
        _reportable_acteur_rows(selection, modele)
        .order_by("suggestion_groupe_id")
        .values_list("suggestion_groupe_id", "champs")
    ):
        plan.setdefault(groupe_id, []).append(champs)
    return plan


def report_plan(cohorte_id: int, modele: str, plan: dict) -> dict:
    """Copies the suggestion of the source to the target of each ligne of the
    plan, groupe by groupe (each groupe in its own transaction)."""
    from data.revue.services import report_lignes

    cohorte = SuggestionCohorte.objects.get(id=cohorte_id)
    policy = get_policy(cohorte.type_action)
    affected = 0
    for groupe_id, champs_list in plan.items():
        with transaction.atomic():
            groupe = (
                groupes_queryset()
                .select_for_update(of=("self",))
                .filter(id=groupe_id)
                .first()
            )
            if groupe is None or groupe.statut != AVALIDER:
                continue
            wanted = {tuple(c) for c in champs_list}
            lignes = [
                ligne
                for ligne in serialize_groupe(groupe, policy)["lignes"]
                if tuple(ligne["champs"]) in wanted
            ]
            if report_lignes(groupe, modele, lignes):
                affected += 1
                SuggestionGroupe.objects.filter(id=groupe_id).update(
                    modifie_le=timezone.now()
                )
    return {"affected": affected}


@task()
def report_task(cohorte_id: int, modele: str, plan: dict) -> dict:
    # JSON keys are strings
    return report_plan(cohorte_id, modele, {int(k): v for k, v in plan.items()})


def _report(selection: Selection, modele: str, total: int) -> dict:
    plan = _report_plan(selection, modele)
    if len(plan) <= SUGGESTION_TASK_ASYNC_THRESHOLD:
        result = report_plan(selection.cohorte.id, modele, plan)
        return {"affected": result["affected"], "skipped": total - result["affected"]}
    task_result = report_task.enqueue(
        selection.cohorte.id, modele, {str(k): v for k, v in plan.items()}
    )
    if task_result.status == TaskResultStatus.SUCCESSFUL:
        # Immediate backend (tests, local): already done
        affected = task_result.return_value["affected"]
        return {"affected": affected, "skipped": total - affected}
    return {"job_id": str(task_result.id), "total": total}


def job_status(job_id: str) -> dict:
    try:
        result = report_task.get_result(job_id)
    except Exception as e:  # ResultDoesNotExist, or a backend without results
        raise RevueApiError(404, "not_found", "Tâche introuvable") from e
    status = {
        TaskResultStatus.READY: "pending",
        TaskResultStatus.RUNNING: "running",
        TaskResultStatus.SUCCESSFUL: "done",
        TaskResultStatus.FAILED: "error",
    }.get(result.status, "pending")
    affected = (
        result.return_value["affected"]
        if result.status == TaskResultStatus.SUCCESSFUL
        else None
    )
    return {"status": status, "affected": affected}
