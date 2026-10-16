"""Structured filters of the review screen (no DjangoQL, no regex).

A filter is a JSON tree sent by the client:
    {"op": "and"|"or", "conditions": [{"field", "operator", "value"} | <tree>]}

Fields come from a server-side whitelist per screen (`FieldSpec`); JSON fields are
addressed by a key path (ex: `metadata.source_code`). The same compiled filter is
used to display, count and run mass actions.
Text comparisons are always case and accent insensitive (unaccent).
"""

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from django.db.models import Expression, Q
from django.db.models.fields.json import KT

from data.revue.errors import RevueApiError

MAX_DEPTH = 3
MAX_CONDITIONS = 30
MAX_IN_VALUES = 100

OPERATORS_BY_TYPE: dict[str, list[str]] = {
    "text": ["eq", "neq", "icontains", "startswith", "in", "is_empty", "is_not_empty"],
    "number": ["eq", "neq", "gt", "lt", "between", "is_empty", "is_not_empty"],
    "date": ["eq", "neq", "gt", "lt", "between", "is_empty", "is_not_empty"],
    "bool": ["eq"],
    "choice": ["eq", "neq", "in"],
    "user": ["eq", "in", "is_empty", "is_not_empty"],
}

# A JSON key: no "__", which the ORM would read as a nested key path
JSON_KEY_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9\-]|_(?!_))*$")


@dataclass(frozen=True)
class FilterContext:
    """Where the filtered rows are, relatively to the fields of the registry.

    - `prefix`: ORM path prepended to the fields paths (ex: "suggestion_groupe__");
    - `groupe_ref`: reference to the groupe id, for the subqueries of expressions;
    - `related`: wrappers of the conditions on related rows, by name
      (ex: "ligne" → Exists(the SuggestionUnitaire of the ligne / of the groupe)).
      A wrapper receives the condition and the annotations it needs.
    """

    prefix: str = ""
    groupe_ref: str = "pk"
    related: dict[str, Callable[[Q, dict], Q]] = field(default_factory=dict)


@dataclass(frozen=True)
class FieldSpec:
    key: str
    label: str
    type: str
    famille: str
    # ORM lookup path, or an expression to annotate (ex: a JSON key)
    path: str | None = None
    expression: Callable[[FilterContext], Expression] | None = None
    choices: tuple[tuple[str, str], ...] = ()
    # datetime fields are compared on their date
    is_datetime: bool = False
    # The condition applies to related rows: compiled on their model, then
    # wrapped by `FilterContext.related[related]`
    related: str | None = None
    # Fully custom condition: builder(context, spec, operator, value) -> Q
    builder: Callable[["FilterContext", "FieldSpec", str, Any], Q] | None = None

    @property
    def operators(self) -> list[str]:
        return OPERATORS_BY_TYPE[self.type]


@dataclass(frozen=True)
class JsonFieldSpec:
    """Dynamic fields `<prefix>.<key>` on a JSON field (text comparison)."""

    prefix: str
    label: str
    famille: str
    path: str

    def field(self, key: str) -> FieldSpec:
        return FieldSpec(
            key=f"{self.prefix}.{key}",
            label=f"{self.label} › {key}",
            type="text",
            famille=self.famille,
            expression=lambda context: KT(f"{context.prefix}{self.path}__{key}"),
        )


@dataclass(frozen=True)
class FieldRegistry:
    fields: tuple[FieldSpec, ...]
    json_fields: tuple[JsonFieldSpec, ...] = ()

    def get(self, key: str) -> FieldSpec:
        for spec in self.fields:
            if spec.key == key:
                return spec
        prefix, _, json_key = key.partition(".")
        for json_spec in self.json_fields:
            if json_spec.prefix == prefix and JSON_KEY_PATTERN.match(json_key or ""):
                return json_spec.field(json_key)
        raise filter_error(f"Champ de filtre inconnu : « {key} »")


def filter_error(detail: str) -> RevueApiError:
    return RevueApiError(422, "invalid_filter", detail)


def parse_filter(raw: str | None) -> dict | None:
    """Parse the `filtre` query parameter (JSON)."""
    if not raw:
        return None
    try:
        tree = json.loads(raw)
    except json.JSONDecodeError as e:
        raise filter_error(f"Filtre JSON invalide : {e}") from e
    return tree


class _Compiler:
    def __init__(self, registry: FieldRegistry, context: FilterContext):
        self.registry = registry
        self.context = context
        self.annotations: dict[str, Expression] = {}
        self.nb_conditions = 0

    def compile(self, node: Any, depth: int = 1) -> Q:
        if not isinstance(node, dict):
            raise filter_error("Chaque élément du filtre doit être un objet")
        if "conditions" in node:
            return self._group(node, depth)
        return self._condition(node)

    def _group(self, node: dict, depth: int) -> Q:
        if depth > MAX_DEPTH:
            raise filter_error(f"Filtre trop imbriqué (au plus {MAX_DEPTH} niveaux)")
        op = node.get("op", "and")
        if op not in ("and", "or"):
            raise filter_error(f"Opérateur logique inconnu : « {op} »")
        conditions = node.get("conditions")
        if not isinstance(conditions, list):
            raise filter_error("« conditions » doit être une liste")
        result = Q()
        for child in conditions:
            q = self.compile(child, depth + 1)
            result = (result | q) if (op == "or" and result) else (result & q)
        return result

    def _alias(self) -> str:
        return f"_filtre_{self.nb_conditions}"

    def _condition(self, node: dict) -> Q:
        self.nb_conditions += 1
        if self.nb_conditions > MAX_CONDITIONS:
            raise filter_error(f"Trop de conditions (au plus {MAX_CONDITIONS})")
        spec = self.registry.get(str(node.get("field", "")))
        operator = node.get("operator")
        if operator not in spec.operators:
            raise filter_error(
                f"Opérateur « {operator} » impossible sur « {spec.label} »"
            )
        value = node.get("value")
        if spec.builder:
            return spec.builder(self.context, spec, operator, value)
        if spec.related:
            # Compiled on the related rows (no prefix), then wrapped
            annotations: dict[str, Expression] = {}
            lhs = spec.path or spec.key
            if spec.expression:
                lhs = self._alias()
                annotations[lhs] = spec.expression(self.context)
            q = self._compare(spec, lhs, operator, value)
            return self.context.related[spec.related](q, annotations)
        lhs = f"{self.context.prefix}{spec.path or spec.key}"
        if spec.expression:
            lhs = self._alias()
            self.annotations[lhs] = spec.expression(self.context)
        return self._compare(spec, lhs, operator, value)

    def _compare(self, spec: FieldSpec, lhs: str, operator: str, value: Any) -> Q:
        if operator in ("is_empty", "is_not_empty"):
            empty = Q(**{f"{lhs}__isnull": True})
            if spec.type == "text":
                empty |= Q(**{lhs: ""})
            return empty if operator == "is_empty" else ~empty
        return {
            "text": self._text,
            "number": self._ordered,
            "date": self._ordered,
            "bool": self._bool,
            "choice": self._choice,
            "user": self._user,
        }[spec.type](spec, lhs, operator, value)

    @staticmethod
    def _text(spec: FieldSpec, lhs: str, operator: str, value: Any) -> Q:
        if operator == "in":
            values = _as_list(value, str, spec)
            q = Q()
            for item in values:
                q |= Q(**{f"{lhs}__unaccent__iexact": item})
            return q
        if not isinstance(value, str):
            raise filter_error(f"Valeur texte attendue pour « {spec.label} »")
        lookup = {
            "eq": "unaccent__iexact",
            "neq": "unaccent__iexact",
            "icontains": "unaccent__icontains",
            "startswith": "unaccent__istartswith",
        }[operator]
        q = Q(**{f"{lhs}__{lookup}": value})
        return ~q if operator == "neq" else q

    @staticmethod
    def _ordered(spec: FieldSpec, lhs: str, operator: str, value: Any) -> Q:
        if spec.is_datetime:
            lhs = f"{lhs}__date"
        cast = _parse_date if spec.type == "date" else _parse_number
        if operator == "between":
            if not isinstance(value, list) or len(value) != 2:
                raise filter_error(f"« entre » attend deux valeurs ({spec.label})")
            low, high = (cast(item, spec) for item in value)
            return Q(**{f"{lhs}__gte": low, f"{lhs}__lte": high})
        value = cast(value, spec)
        if operator == "neq":
            return ~Q(**{lhs: value})
        lookup = {"eq": "", "gt": "__gt", "lt": "__lt"}[operator]
        return Q(**{f"{lhs}{lookup}": value})

    @staticmethod
    def _bool(spec: FieldSpec, lhs: str, operator: str, value: Any) -> Q:
        if not isinstance(value, bool):
            raise filter_error(f"Valeur oui/non attendue pour « {spec.label} »")
        return Q(**{lhs: value})

    @staticmethod
    def _choice(spec: FieldSpec, lhs: str, operator: str, value: Any) -> Q:
        allowed = {choice for choice, _ in spec.choices}
        values = _as_list(value, str, spec) if operator == "in" else [value]
        if unknown := [item for item in values if item not in allowed]:
            raise filter_error(f"Valeur inconnue pour « {spec.label} » : {unknown}")
        if operator == "in":
            return Q(**{f"{lhs}__in": values})
        q = Q(**{lhs: value})
        return ~q if operator == "neq" else q

    @staticmethod
    def _user(spec: FieldSpec, lhs: str, operator: str, value: Any) -> Q:
        if operator == "in":
            return Q(**{f"{lhs}__in": _as_list(value, int, spec)})
        if not isinstance(value, int) or isinstance(value, bool):
            raise filter_error(f"Identifiant d'utilisateur attendu ({spec.label})")
        return Q(**{lhs: value})


def _as_list(value: Any, item_type: type, spec: FieldSpec) -> list:
    if (
        not isinstance(value, list)
        or not value
        or len(value) > MAX_IN_VALUES
        or not all(
            isinstance(item, item_type) and not isinstance(item, bool) for item in value
        )
    ):
        raise filter_error(
            f"« parmi » attend une liste de 1 à {MAX_IN_VALUES} valeurs ({spec.label})"
        )
    return value


def _parse_number(value: Any, spec: FieldSpec) -> int | float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise filter_error(f"Nombre attendu pour « {spec.label} »")
    return value


def _parse_date(value: Any, spec: FieldSpec) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as e:
        raise filter_error(f"Date AAAA-MM-JJ attendue pour « {spec.label} »") from e


def compile_filter(
    tree: dict | None, registry: FieldRegistry, context: FilterContext | None = None
) -> tuple[dict[str, Expression], Q]:
    """Compile a filter tree into (annotations to add with `.alias()`, Q)."""
    if not tree:
        return {}, Q()
    compiler = _Compiler(registry, context or FilterContext())
    q = compiler.compile(tree)
    return compiler.annotations, q


def apply_filter(
    queryset,
    tree: dict | None,
    registry: FieldRegistry | None,
    context: FilterContext | None = None,
):
    if not tree:
        return queryset
    annotations, q = compile_filter(tree, registry, context)
    if annotations:
        queryset = queryset.alias(**annotations)
    return queryset.filter(q)


def registry_metadata(registry: FieldRegistry, json_keys: dict[str, list[str]]):
    """Fields description sent to the filter builder (`FilterMetaOut`)."""
    fields = list(registry.fields)
    for json_spec in registry.json_fields:
        fields += [json_spec.field(key) for key in json_keys.get(json_spec.prefix, [])]
    return [
        {
            "key": spec.key,
            "label": spec.label,
            "famille": spec.famille,
            "type": spec.type,
            "operateurs": spec.operators,
            "choix": [
                {"value": str(value), "label": label} for value, label in spec.choices
            ]
            or None,
        }
        for spec in fields
    ]
