"""Background tasks (django-tasks) of a cohorte, for the « Tâches » panel.

The database backend keeps the arguments of each task (DBTaskResult.args_kwargs):
a task of the review screen is attached to its cohorte by its first argument, so
no extra model is needed."""

from django.db.models import F
from django.db.models.expressions import RawSQL
from django_tasks_db.models import DBTaskResult

from data.models.suggestion import SuggestionCohorte
from data.revue.masse import TASK_STATUTS, report_task
from data.revue.policies import PARENT, REVISION

LIMIT = 100

# Number of groupes of the plan (3rd argument), counted by PostgreSQL so that the
# plans (one entry per groupe) are not loaded at each refresh
PLAN_SIZE = RawSQL(
    "(SELECT count(*) FROM jsonb_object_keys(args_kwargs -> 'args' -> 2))", []
)
ACTIONS = {REVISION: "report_correction", PARENT: "report_parent"}


def cohorte_taches(cohorte: SuggestionCohorte) -> list[dict]:
    """The report tasks of the cohorte, most recent first."""
    rows = (
        DBTaskResult.objects.filter(
            task_path=report_task.module_path, args_kwargs__args__0=cohorte.id
        )
        .annotate(groupes=PLAN_SIZE)
        .order_by("-enqueued_at")
        .values(
            "id",
            "status",
            "enqueued_at",
            "started_at",
            "finished_at",
            "groupes",
            "exception_class_path",
            modele=F("args_kwargs__args__1"),
            par=F("args_kwargs__kwargs__par"),
            affected=F("return_value__affected"),
        )[:LIMIT]
    )
    return [
        {
            "id": str(row["id"]),
            "statut": TASK_STATUTS.get(row["status"], "pending"),
            "action": ACTIONS[row["modele"]],
            "groupes": row["groupes"],
            "affected": row["affected"],
            "par": row["par"] or "",
            "lancee_le": row["enqueued_at"],
            "debut": row["started_at"],
            "fin": row["finished_at"],
            "erreur": row["exception_class_path"].rsplit(".", 1)[-1],
        }
        for row in rows
    ]
