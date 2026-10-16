"""Screen 2: review of a cohorte, views « Groupes » and « Lignes ».

Both views share the same filters, with the same labels. A field targets either
the groupe (and its acteur) or the ligne de suggestion:
- in the Groupes view, a condition on the ligne keeps the groupes having at least
  one ligne matching it (two ET conditions may match two different lignes);
- in the Lignes view, a condition on the groupe applies to the groupe of the ligne.
Lignes are rows of SuggestionUnitaire grouped by (groupe, champs).
"""

from typing import Literal

from django.contrib.auth import get_user_model
from django.db.models import (
    BooleanField,
    Case,
    Expression,
    IntegerField,
    When,
    CharField,
    Count,
    Exists,
    ExpressionWrapper,
    F,
    Func,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    TextField,
    Value,
)
from django.db.models.functions import Cast, Coalesce, Concat

from data.models.suggestion import (
    SuggestionCohorte,
    SuggestionGroupe,
    SuggestionStatut,
    SuggestionUnitaire,
)
from data.revue.errors import RevueApiError
from data.revue.filters import (
    FieldRegistry,
    FieldSpec,
    FilterContext,
    JsonFieldSpec,
    _Compiler,
    apply_filter,
    filter_error,
    registry_metadata,
)
from data.revue.lignes import ACTEUR, ORDERED_FIELDS, ordered_champs
from data.revue.policies import PARENT, REVISION

Vue = Literal["groupes", "lignes"]
Afficher = Literal["avalider", "tout"]

PAGE_SIZE_MAX = {"groupes": 200, "lignes": 1000}

STATUT_CHOICES = tuple(SuggestionStatut.choices)
COLONNES = {"correction": REVISION, "parent": PARENT}


# --- Contexts of the two views ---


def _sus_of(context_view: Vue) -> QuerySet:
    """SuggestionUnitaire of the outer row: of the groupe, or of the ligne."""
    if context_view == "groupes":
        return SuggestionUnitaire.objects.filter(suggestion_groupe_id=OuterRef("pk"))
    return SuggestionUnitaire.objects.filter(
        suggestion_groupe_id=OuterRef("suggestion_groupe_id"),
        champs=OuterRef("champs"),
    )


def filter_context(vue: Vue) -> FilterContext:
    def ligne(q: Q, annotations: dict) -> Q:
        return Q(Exists(_sus_of(vue).alias(**annotations).filter(q)))

    if vue == "groupes":
        return FilterContext(prefix="", groupe_ref="pk", related={"ligne": ligne})
    return FilterContext(
        prefix="suggestion_groupe__",
        groupe_ref="suggestion_groupe_id",
        related={"ligne": ligne},
    )


def _vue_of(context: FilterContext) -> Vue:
    return "groupes" if context.groupe_ref == "pk" else "lignes"


# --- Ligne statut (derived) ---


def _not_validated_sus(vue: Vue) -> QuerySet:
    return _sus_of(vue).exclude(statut=SuggestionStatut.ATRAITER)


def ligne_statut_q(vue: Vue, statut: str, prefix: str) -> Q:
    """Rows (groupes: having at least one ligne / lignes) whose ligne statut is…"""
    groupe_statut = f"{prefix}statut"
    if statut == SuggestionStatut.AVALIDER:
        return Q(**{groupe_statut: SuggestionStatut.AVALIDER}) & Q(
            Exists(_not_validated_sus(vue))
        )
    if statut == SuggestionStatut.ATRAITER:
        if vue == "groupes":
            # A ligne all of whose SU are validated
            fully_validated = SuggestionUnitaire.objects.filter(
                suggestion_groupe_id=OuterRef("pk"), statut=SuggestionStatut.ATRAITER
            ).exclude(
                Exists(
                    SuggestionUnitaire.objects.filter(
                        suggestion_groupe_id=OuterRef("suggestion_groupe_id"),
                        champs=OuterRef("champs"),
                    ).exclude(statut=SuggestionStatut.ATRAITER)
                )
            )
            validated_ligne = Q(Exists(fully_validated))
        else:
            validated_ligne = ~Q(Exists(_not_validated_sus(vue)))
        return Q(**{groupe_statut: SuggestionStatut.ATRAITER}) | (
            Q(**{groupe_statut: SuggestionStatut.AVALIDER}) & validated_ligne
        )
    return Q(**{groupe_statut: statut})


def _ligne_statut_builder(context: FilterContext, spec, operator, value) -> Q:
    allowed = [choice for choice, _ in STATUT_CHOICES]
    values = value if operator == "in" else [value]
    if (
        not isinstance(values, list)
        or not values
        or any(item not in allowed for item in values)
    ):
        raise filter_error(f"Valeur inconnue pour « {spec.label} » : {value}")
    if operator == "neq":
        values = [item for item in allowed if item != value]
    vue = _vue_of(context)
    q = Q(pk__in=[])
    for item in values:
        q |= ligne_statut_q(vue, item, context.prefix)
    return q


def _colonne_builder(context: FilterContext, spec, operator, value) -> Q:
    values = value if operator == "in" else [value]
    if not isinstance(values, list) or any(item not in COLONNES for item in values):
        raise filter_error(f"Valeur inconnue pour « {spec.label} » : {value}")
    has = Q(pk__in=[])
    for item in values:
        has |= Q(suggestion_modele=COLONNES[item])
    q = context.related["ligne"](has, {})
    return ~q if operator == "neq" else q


def _champs_builder(context: FilterContext, spec, operator, value) -> Q:
    """Tuple de champs, written « champ,champ »."""
    values = value if operator == "in" else [value]
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        raise filter_error(f"Tuple de champs attendu pour « {spec.label} »")
    q = Q(champs__in=[item.split(",") for item in values])
    wrapped = context.related["ligne"](q, {})
    return ~wrapped if operator == "neq" else wrapped


# --- Expressions ---


def _valeurs_text():
    return Func(
        F("valeurs"), Value(" | "), function="array_to_string", output_field=TextField()
    )


def _acteur_field(champ: str):
    """Field of the acteur, or value suggested by the source when the acteur does
    not exist yet (AJOUT)."""

    def expression(context: FilterContext):
        suggested = SuggestionUnitaire.objects.filter(
            suggestion_groupe_id=OuterRef(context.groupe_ref),
            suggestion_modele=ACTEUR,
            champs=[champ],
        ).values("valeurs__0")[:1]
        return Coalesce(
            Cast(F(f"{context.prefix}acteur__{champ}"), CharField()),
            Subquery(suggested, output_field=CharField()),
        )

    return expression


def _is_set(path: str):
    return ExpressionWrapper(
        Q(**{f"{path}__isnull": False}), output_field=BooleanField()
    )


def _nb_lignes(context: FilterContext):
    lignes = (
        SuggestionUnitaire.objects.filter(
            suggestion_groupe_id=OuterRef(context.groupe_ref)
        )
        .order_by()
        .values("suggestion_groupe_id")
        .annotate(n=Count("champs", distinct=True))
        .values("n")
    )
    return Coalesce(Subquery(lignes), 0)


class ActeurValueMatches(Expression):
    """Whether the current value of the acteur, for one of the champs of the ligne,
    matches a text comparison (case and accent insensitive).

    The acteur row is read as JSON (`to_jsonb`), its fields being named like the
    champs of the suggestions. Only usable on SuggestionUnitaire rows."""

    output_field = BooleanField()
    conditional = True
    COMPARISONS = {
        "eq": "= unaccent(lower(%s))",
        "icontains": "LIKE '%%' || unaccent(lower(%s)) || '%%'",
        "startswith": "LIKE unaccent(lower(%s)) || '%%'",
    }

    def __init__(self, comparison: str, value: str = "", champs=None, acteur=None):
        super().__init__()
        self.comparison = comparison
        self.value = value
        self.champs = champs if champs is not None else F("champs")
        self.acteur = (
            acteur if acteur is not None else F("suggestion_groupe__acteur_id")
        )

    def get_source_expressions(self):
        return [self.champs, self.acteur]

    def set_source_expressions(self, expressions):
        self.champs, self.acteur = expressions

    def as_sql(self, compiler, connection):
        champs_sql, champs_params = compiler.compile(self.champs)
        acteur_sql, acteur_params = compiler.compile(self.acteur)
        current = "unaccent(lower(_acteur_json ->> _champ))"
        if self.comparison == "is_empty":
            condition, params = f"coalesce({current}, '') = ''", []
        else:
            comparison = self.COMPARISONS[self.comparison]
            condition = f"{current} {comparison}"
            params = [_escape_like(self.value) if "LIKE" in comparison else self.value]
        sql = (
            "EXISTS (SELECT 1 FROM qfdmo_acteur _acteur"
            " CROSS JOIN LATERAL to_jsonb(_acteur) AS _acteur_json"
            f" CROSS JOIN LATERAL unnest({champs_sql}) AS _champ"
            f" WHERE _acteur.identifiant_unique = {acteur_sql} AND {condition})"
        )
        return sql, (*champs_params, *acteur_params, *params)


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _acteur_value_builder(context: FilterContext, spec, operator, value) -> Q:
    """Current value of the acteur (Acteur importé, before the suggestion)."""
    if operator in ("is_empty", "is_not_empty"):
        q = context.related["ligne"](Q(ActeurValueMatches("is_empty")), {})
        return q if operator == "is_empty" else ~q
    values = value if operator == "in" else [value]
    if (
        not isinstance(values, list)
        or not values
        or not all(isinstance(item, str) for item in values)
    ):
        raise filter_error(f"Valeur texte attendue pour « {spec.label} »")
    comparison = "eq" if operator in ("eq", "neq", "in") else operator
    q = Q(pk__in=[])
    for item in values:
        q |= context.related["ligne"](Q(ActeurValueMatches(comparison, item)), {})
    return ~q if operator == "neq" else q


# --- Registry ---


def review_registry(cohorte: SuggestionCohorte) -> FieldRegistry:
    groupes = cohorte.suggestion_groupes.all()
    tuples = ordered_champs(
        tuple(champs)
        for champs in SuggestionUnitaire.objects.filter(
            suggestion_groupe__suggestion_cohorte=cohorte
        )
        .values_list("champs", flat=True)
        .distinct()
    )
    user_ids = set(
        groupes.exclude(decision_par=None).values_list("decision_par", flat=True)
    )
    user_ids |= set(
        SuggestionUnitaire.objects.filter(suggestion_groupe__suggestion_cohorte=cohorte)
        .exclude(decision_par=None)
        .values_list("decision_par", flat=True)
        .distinct()
    )
    users = tuple(
        (user.id, user.get_username())
        for user in get_user_model()
        .objects.filter(id__in=user_ids)
        .order_by("username")
    )
    tuple_choices = tuple((",".join(t), " + ".join(t)) for t in tuples)
    champ_choices = tuple(
        (champ, champ) for champ in sorted({champ for t in tuples for champ in t})
    )

    def on_ligne(key, label, type_, path=None, **kwargs):
        return FieldSpec(
            key, label, type_, "ligne", path=path, related="ligne", **kwargs
        )

    return FieldRegistry(
        fields=(
            # Groupe et acteur
            FieldSpec("groupe.id", "Id du groupe", "number", "groupe", path="id"),
            FieldSpec(
                "groupe.statut",
                "Statut du groupe",
                "choice",
                "groupe",
                path="statut",
                choices=STATUT_CHOICES,
            ),
            FieldSpec(
                "groupe.a_parent",
                "Le groupe a un parent",
                "bool",
                "groupe",
                expression=lambda c: _is_set(f"{c.prefix}parent_revision_acteur_id"),
            ),
            FieldSpec(
                "groupe.a_correction",
                "Le groupe a une correction existante",
                "bool",
                "groupe",
                expression=lambda c: _is_set(f"{c.prefix}revision_acteur_id"),
            ),
            FieldSpec(
                "groupe.nb_lignes",
                "Nombre de lignes du groupe",
                "number",
                "groupe",
                expression=_nb_lignes,
            ),
            FieldSpec(
                "groupe.decision_par",
                "Groupe décidé par",
                "user",
                "groupe",
                path="decision_par_id",
                choices=users,
            ),
            FieldSpec(
                "groupe.decision_le",
                "Groupe décidé le",
                "date",
                "groupe",
                path="decision_le",
                is_datetime=True,
            ),
            *(
                FieldSpec(
                    f"acteur.{champ}",
                    label,
                    "text",
                    "groupe",
                    expression=_acteur_field(champ),
                )
                for champ, label in (
                    ("nom", "Nom de l'acteur"),
                    ("identifiant_unique", "identifiant_unique de l'acteur"),
                    ("identifiant_externe", "identifiant_externe de l'acteur"),
                    ("ville", "Ville de l'acteur"),
                )
            ),
            # Ligne de suggestion
            FieldSpec(
                "ligne.champs",
                "Tuple de champs de la ligne",
                "choice",
                "ligne",
                choices=tuple_choices,
                builder=_champs_builder,
            ),
            FieldSpec(
                "ligne.champ",
                "Champ modifié par la ligne",
                "choice",
                "ligne",
                choices=champ_choices,
                builder=_champ_builder,
            ),
            FieldSpec(
                "ligne.statut",
                "Statut de la ligne",
                "choice",
                "ligne",
                choices=STATUT_CHOICES,
                builder=_ligne_statut_builder,
            ),
            on_ligne(
                "ligne.decision_par",
                "Ligne décidée par",
                "user",
                path="decision_par_id",
                choices=users,
            ),
            on_ligne(
                "ligne.decision_le",
                "Ligne décidée le",
                "date",
                path="decision_le",
                is_datetime=True,
            ),
            *(
                FieldSpec(
                    key,
                    label,
                    "text",
                    "ligne",
                    builder=_valeurs_builder(modele),
                )
                for key, label, modele in (
                    (
                        "ligne.valeur_source",
                        "Valeur suggérée par la source (Acteur importé)",
                        ACTEUR,
                    ),
                    (
                        "ligne.valeur_correction",
                        "Valeur proposée en correction",
                        REVISION,
                    ),
                    ("ligne.valeur_parent", "Valeur proposée sur le parent", PARENT),
                )
            ),
            FieldSpec(
                "ligne.valeur_actuelle",
                "Valeur actuelle de l'acteur (avant la suggestion)",
                "text",
                "ligne",
                builder=_acteur_value_builder,
            ),
            FieldSpec(
                "ligne.colonne",
                "Colonne portant une proposition",
                "choice",
                "ligne",
                choices=(("correction", "Correction"), ("parent", "Parent")),
                builder=_colonne_builder,
            ),
        ),
        json_fields=(
            JsonFieldSpec("contexte", "Contexte du groupe", "groupe", path="contexte"),
        ),
    )


def _champ_builder(context: FilterContext, spec, operator, value) -> Q:
    values = value if operator == "in" else [value]
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        raise filter_error(f"Nom de champ attendu pour « {spec.label} »")
    q = Q(pk__in=[])
    for item in values:
        q |= Q(champs__contains=[item])
    wrapped = context.related["ligne"](q, {})
    return ~wrapped if operator == "neq" else wrapped


def _valeurs_builder(modele: str):
    """Value of the SU of a column (all champs of the ligne, joined with « | »)."""

    def builder(context: FilterContext, spec, operator, value) -> Q:
        if operator in ("is_empty", "is_not_empty"):
            has = context.related["ligne"](Q(suggestion_modele=modele), {})
            return ~has if operator == "is_empty" else has
        # Same (unaccent, case insensitive) text comparisons as the other fields
        q = _Compiler._text(spec, "valeurs_texte", operator, value)
        return context.related["ligne"](
            Q(suggestion_modele=modele) & q, {"valeurs_texte": _valeurs_text()}
        )

    return builder


# --- Querysets ---


def review_filter_metadata(cohorte: SuggestionCohorte) -> list[dict]:
    keys = (
        cohorte.suggestion_groupes.annotate(
            json_type=Func(
                "contexte", function="jsonb_typeof", output_field=TextField()
            )
        )
        .filter(json_type="object")
        .annotate(
            key=Func("contexte", function="jsonb_object_keys", output_field=TextField())
        )
        .values_list("key", flat=True)
        .distinct()
        .order_by("key")
    )
    return registry_metadata(review_registry(cohorte), {"contexte": list(keys)})


def _tuples_q(tuples: list[list[str]], vue: Vue) -> Q:
    if not tuples:
        return Q()
    if vue == "groupes":
        return Q(
            Exists(
                SuggestionUnitaire.objects.filter(
                    suggestion_groupe_id=OuterRef("pk"), champs__in=tuples
                )
            )
        )
    return Q(champs__in=tuples)


def filtered_groupes(
    cohorte: SuggestionCohorte,
    filtre: dict | None,
    tuples: list[list[str]],
    afficher: Afficher | None,
    registry: FieldRegistry | None = None,
) -> QuerySet[SuggestionGroupe]:
    if filtre and registry is None:
        registry = review_registry(cohorte)
    queryset = apply_filter(
        cohorte.suggestion_groupes.all(),
        filtre,
        registry,
        filter_context("groupes"),
    ).filter(_tuples_q(tuples, "groupes"))
    if afficher == "avalider":
        queryset = queryset.filter(statut=SuggestionStatut.AVALIDER)
    return queryset


def filtered_ligne_rows(
    cohorte: SuggestionCohorte,
    filtre: dict | None,
    tuples: list[list[str]],
    afficher: Afficher | None,
    registry: FieldRegistry | None = None,
) -> QuerySet[SuggestionUnitaire]:
    """SuggestionUnitaire rows of the lignes matching the filter: every SU of a
    ligne matches or not, since conditions only depend on (groupe, champs)."""
    if filtre and registry is None:
        registry = review_registry(cohorte)
    queryset = apply_filter(
        SuggestionUnitaire.objects.filter(
            suggestion_groupe__suggestion_cohorte=cohorte
        ),
        filtre,
        registry,
        filter_context("lignes"),
    ).filter(_tuples_q(tuples, "lignes"))
    if afficher == "avalider":
        queryset = queryset.filter(
            ligne_statut_q("lignes", SuggestionStatut.AVALIDER, "suggestion_groupe__")
        )
    return queryset


def lignes_page(
    cohorte: SuggestionCohorte,
    filtre: dict | None,
    tuples: list[list[str]],
    afficher: Afficher | None,
    page: int,
    page_size: int,
) -> tuple[list[tuple[int, list[str]]], int]:
    """(groupe id, champs) of the lignes of a page, ordered by groupe then as the
    admin orders the champs, and the total number of lignes."""
    order = Case(
        *(
            When(champs=list(fields), then=Value(i))
            for i, fields in enumerate(ORDERED_FIELDS)
        ),
        default=Value(len(ORDERED_FIELDS)),
        output_field=IntegerField(),
    )
    lignes = (
        filtered_ligne_rows(cohorte, filtre, tuples, afficher)
        .order_by()
        .values("suggestion_groupe_id", "champs")
        .distinct()
        .annotate(rang=order)
        .order_by("suggestion_groupe_id", "rang", "champs")
    )
    total = lignes.count()
    offset = (page - 1) * page_size
    keys = [
        (row["suggestion_groupe_id"], row["champs"])
        for row in lignes[offset : offset + page_size]
    ]
    return keys, total


def _ligne_key_expression():
    return Concat(
        Cast("suggestion_groupe_id", TextField()),
        Value(":"),
        Func(
            F("champs"),
            Value(","),
            function="array_to_string",
            output_field=TextField(),
        ),
        output_field=TextField(),
    )


def count_lignes_by_statut(rows: QuerySet[SuggestionUnitaire]) -> dict[str, int]:
    """Lignes per (derived) statut, without loading them."""
    key = _ligne_key_expression()
    counts = {statut: 0 for statut in SuggestionStatut.values}
    for row in (
        rows.order_by()
        .values("suggestion_groupe__statut")
        .annotate(
            total=Count(key, distinct=True),
            open=Count(key, distinct=True, filter=~Q(statut=SuggestionStatut.ATRAITER)),
        )
    ):
        groupe_statut = row["suggestion_groupe__statut"]
        if groupe_statut == SuggestionStatut.AVALIDER:
            counts[SuggestionStatut.AVALIDER] += row["open"]
            counts[SuggestionStatut.ATRAITER] += row["total"] - row["open"]
        else:
            counts[groupe_statut] += row["total"]
    return counts


def stats(
    cohorte: SuggestionCohorte,
    vue: Vue,
    filtre: dict | None,
    tuples: list[list[str]],
    afficher: Afficher | None,
) -> dict:
    """Counters of the header (unit of the view, all statuts, ignoring
    « afficher »), size of each view, and counts per tuple."""
    registry = review_registry(cohorte) if filtre else None
    if vue == "groupes":
        counts = {statut: 0 for statut in SuggestionStatut.values}
        for row in (
            filtered_groupes(cohorte, filtre, tuples, None, registry)
            .order_by()
            .values("statut")
            .annotate(n=Count("id"))
        ):
            counts[row["statut"]] = row["n"]
    else:
        counts = count_lignes_by_statut(
            filtered_ligne_rows(cohorte, filtre, tuples, None, registry)
        )

    nb_groupes = filtered_groupes(cohorte, filtre, tuples, afficher, registry).count()
    nb_lignes = (
        filtered_ligne_rows(cohorte, filtre, tuples, afficher, registry)
        .order_by()
        .aggregate(n=Count(_ligne_key_expression(), distinct=True))["n"]
    )

    if vue == "groupes":
        tuple_counts = (
            SuggestionUnitaire.objects.filter(
                suggestion_groupe__in=filtered_groupes(
                    cohorte, filtre, [], afficher, registry
                )
            )
            .order_by()
            .values("champs")
            .annotate(n=Count("suggestion_groupe_id", distinct=True))
        )
    else:
        tuple_counts = (
            filtered_ligne_rows(cohorte, filtre, [], afficher, registry)
            .order_by()
            .values("champs")
            .annotate(n=Count("suggestion_groupe_id", distinct=True))
        )
    by_tuple = {tuple(row["champs"]): row["n"] for row in tuple_counts}
    return {
        "compteurs": counts,
        "totaux_vues": {"groupes": nb_groupes, "lignes": nb_lignes},
        "tuples": [
            {"champs": list(champs), "count": by_tuple[champs]}
            for champs in ordered_champs(by_tuple)
        ],
    }


def parse_tuples(raw: list[str]) -> list[list[str]]:
    tuples = [item.split(",") for item in raw if item]
    if any(not all(tuples_item) for tuples_item in tuples):
        raise RevueApiError(422, "invalid_tuples", "Tuple de champs invalide")
    return tuples
