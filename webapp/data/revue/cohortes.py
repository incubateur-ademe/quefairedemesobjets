"""Screen 1: list of the SOURCE cohortes, and their logs."""

from datetime import date

from django.db.models import (
    Case,
    Count,
    Func,
    IntegerField,
    Q,
    QuerySet,
    TextField,
    Value,
    When,
)
from django.shortcuts import get_object_or_404

from data.models.suggestion import (
    SOURCE_TYPE_ACTIONS,
    SuggestionAction,
    SuggestionCohorte,
    SuggestionCohorteStatut,
    SuggestionGroupe,
    SuggestionLog,
    SuggestionStatut,
)
from data.revue.errors import RevueApiError
from data.revue.filters import (
    FieldRegistry,
    FieldSpec,
    JsonFieldSpec,
    apply_filter,
    registry_metadata,
)
from data.revue.pagination import paginate

SOURCE_TYPE_ACTION_CHOICES = tuple(
    (value, label)
    for value, label in SuggestionAction.choices
    if value in SOURCE_TYPE_ACTIONS
)

COHORTE_FIELDS = FieldRegistry(
    fields=(
        FieldSpec("id", "Id de la cohorte", "number", "cohorte"),
        FieldSpec("identifiant_action", "Identifiant de l'action", "text", "cohorte"),
        FieldSpec(
            "identifiant_execution", "Identifiant de l'exécution", "text", "cohorte"
        ),
        FieldSpec(
            "type_action",
            "Type d'action",
            "choice",
            "cohorte",
            choices=SOURCE_TYPE_ACTION_CHOICES,
        ),
        FieldSpec(
            "statut",
            "Statut de la cohorte",
            "choice",
            "cohorte",
            choices=tuple(SuggestionCohorteStatut.choices),
        ),
        FieldSpec("cree_le", "Date de création", "date", "cohorte", is_datetime=True),
    ),
    json_fields=(JsonFieldSpec("metadata", "Métadonnées", "cohorte", path="metadata"),),
)

SORTS = {
    "id": "id",
    "identifiant_action": "identifiant_action",
    "identifiant_execution": "identifiant_execution",
    "type_action": "type_action",
    "statut": "statut",
    "cree_le": "cree_le",
    "total_groupes": "total_groupes",
    "avalider": "nb_avalider",
}
DEFAULT_SORT = "-cree_le"

LOG_LEVELS = [
    SuggestionLog.SuggestionLogLevel.ERROR,
    SuggestionLog.SuggestionLogLevel.WARNING,
    SuggestionLog.SuggestionLogLevel.INFO,
]


def source_cohortes() -> QuerySet[SuggestionCohorte]:
    """SOURCE cohortes having at least one groupe."""
    return (
        SuggestionCohorte.objects.filter(type_action__in=SOURCE_TYPE_ACTIONS)
        .annotate(
            total_groupes=Count("suggestion_groupes"),
            nb_avalider=Count(
                "suggestion_groupes",
                filter=Q(suggestion_groupes__statut=SuggestionStatut.AVALIDER),
            ),
        )
        .filter(total_groupes__gt=0)
    )


def get_source_cohorte(cohorte_id: int) -> SuggestionCohorte:
    return get_object_or_404(
        SuggestionCohorte, id=cohorte_id, type_action__in=SOURCE_TYPE_ACTIONS
    )


def _order_by(tri: str | None) -> list[str]:
    tri = tri or DEFAULT_SORT
    descending = tri.startswith("-")
    key = tri.removeprefix("-")
    if key not in SORTS:
        raise RevueApiError(422, "invalid_sort", f"Tri impossible sur « {key} »")
    field = f"{'-' if descending else ''}{SORTS[key]}"
    return [field, "-id"] if key != "id" else [field]


def cohortes_page(
    *,
    filtre: dict | None,
    type_action: list[str],
    statut: list[str],
    cree_apres: date | None,
    cree_avant: date | None,
    tri: str | None,
    page: int,
    page_size: int,
) -> dict:
    queryset = apply_filter(source_cohortes(), filtre, COHORTE_FIELDS)
    if type_action:
        queryset = queryset.filter(type_action__in=type_action)
    if statut:
        queryset = queryset.filter(statut__in=statut)
    if cree_apres:
        queryset = queryset.filter(cree_le__date__gte=cree_apres)
    if cree_avant:
        queryset = queryset.filter(cree_le__date__lte=cree_avant)
    items, total = paginate(queryset.order_by(*_order_by(tri)), page, page_size)
    _attach_counts(items)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def _attach_counts(cohortes: list[SuggestionCohorte]) -> None:
    """Groupes per statut and logs per level, with one grouped query each."""
    ids = [cohorte.id for cohorte in cohortes]
    groupes = {}
    for row in (
        SuggestionGroupe.objects.filter(suggestion_cohorte_id__in=ids)
        .values("suggestion_cohorte_id", "statut")
        .annotate(n=Count("id"))
    ):
        groupes.setdefault(row["suggestion_cohorte_id"], {})[row["statut"]] = row["n"]
    logs = {}
    for row in (
        SuggestionLog.objects.filter(suggestion_cohorte_id__in=ids)
        .values("suggestion_cohorte_id", "niveau_de_log")
        .annotate(n=Count("id"))
    ):
        logs.setdefault(row["suggestion_cohorte_id"], {})[row["niveau_de_log"]] = row[
            "n"
        ]
    for cohorte in cohortes:
        cohorte.compteurs = {
            statut: groupes.get(cohorte.id, {}).get(statut, 0)
            for statut in SuggestionStatut.values
        }
        cohorte.logs = {
            level: logs.get(cohorte.id, {}).get(level, 0) for level in LOG_LEVELS
        }


def cohortes_filter_metadata() -> list[dict]:
    metadata_keys = (
        SuggestionCohorte.objects.filter(type_action__in=SOURCE_TYPE_ACTIONS)
        .annotate(
            json_type=Func(
                "metadata", function="jsonb_typeof", output_field=TextField()
            )
        )
        .filter(json_type="object")
        .annotate(
            key=Func("metadata", function="jsonb_object_keys", output_field=TextField())
        )
        .values_list("key", flat=True)
        .distinct()
        .order_by("key")
    )
    return registry_metadata(COHORTE_FIELDS, {"metadata": list(metadata_keys)})


def logs_page(
    cohorte: SuggestionCohorte, niveau: list[str], page: int, page_size: int
) -> dict:
    gravity = Case(
        *(
            When(niveau_de_log=level, then=Value(gravite))
            for gravite, level in enumerate(LOG_LEVELS)
        ),
        default=Value(len(LOG_LEVELS)),
        output_field=IntegerField(),
    )
    queryset = cohorte.suggestion_logs.annotate(gravite=gravity)
    if niveau:
        queryset = queryset.filter(niveau_de_log__in=niveau)
    items, total = paginate(
        queryset.order_by("gravite", "-cree_le", "-id"), page, page_size
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}
