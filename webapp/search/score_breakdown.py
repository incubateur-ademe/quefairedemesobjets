"""Per-result score breakdown for the autocomplete debug panel.

Exposed only to users with the ``wagtailadmin.can_see_beta_search`` permission
(beta mode, see ``qfdmd.middleware.BetaMiddleware``). Lets us inspect why a
given SearchTerm matched a query: similarity per indexed field, title-length
normalisation factor and prefix bonus.

Mirrors the math run by the modelsearch postgres backend in
``modelsearch.backends.database.postgres._build_fuzzy_queryset`` so the values
shown here line up with the actual ranking. If the backend ever changes its
formula, this module has to follow.
"""

from dataclasses import dataclass

from django.conf import settings
from django.contrib.postgres.search import TrigramWordSimilarity
from django.db.models import Case, F, Func, TextField, Value, When


class _FUnaccent(Func):
    """Local mirror of modelsearch's f_unaccent() wrapper.

    Duplicated rather than imported because modelsearch's class is private
    (lives under ``backends.database.postgres``) and importing across that
    boundary couples us to internal layout.
    """

    function = "f_unaccent"
    output_field = TextField()


@dataclass(frozen=True)
class ScoreBreakdown:
    title_sim: float
    body_sim: float
    title_norm: float
    is_prefix: bool

    @property
    def prefix_multiplier(self) -> float:
        boost = settings.MODELSEARCH_BACKENDS["default"].get("FUZZY_PREFIX_BOOST", 0.0)
        return 1.0 + boost if self.is_prefix else 1.0

    @property
    def ranked(self) -> float:
        """Final ranking score, same formula the postgres backend uses."""
        return (
            max(self.title_sim * self.title_norm, self.body_sim)
            * self.prefix_multiplier
        )

    @property
    def raw(self) -> float:
        """Pre-normalisation similarity, the value compared to the threshold."""
        return max(self.title_sim, self.body_sim)


def compute_breakdown(
    query: str, search_term_pks: list[int]
) -> dict[int, ScoreBreakdown]:
    """Return per-pk score breakdown for the given SearchTerm pks.

    Runs one extra SQL query annotated with each component of the score
    formula. ``query`` is the unaccent-normalised search string the user
    typed; ``search_term_pks`` is the list of SearchTerm ids retained by the
    autocomplete (typically the 7 displayed ones).
    """
    if not query or not search_term_pks:
        return {}

    # Lazy import to avoid pulling search models at app import time.
    from search.models import SearchTerm

    normalised_query = _FUnaccent(Value(query, output_field=TextField()))

    rows = (
        SearchTerm.objects.filter(pk__in=search_term_pks)
        .annotate(
            _title_text=F("index_entries__title_text"),
            _body_text=F("index_entries__body_text"),
            _title_norm=F("index_entries__title_norm"),
            _title_sim=TrigramWordSimilarity(
                normalised_query, _FUnaccent(F("index_entries__title_text"))
            ),
            _body_sim=TrigramWordSimilarity(
                normalised_query, _FUnaccent(F("index_entries__body_text"))
            ),
            _is_prefix=Case(
                When(index_entries__title_text__istartswith=query, then=Value(True)),
                default=Value(False),
            ),
        )
        .values("pk", "_title_sim", "_body_sim", "_title_norm", "_is_prefix")
    )

    return {
        row["pk"]: ScoreBreakdown(
            title_sim=float(row["_title_sim"] or 0.0),
            body_sim=float(row["_body_sim"] or 0.0),
            title_norm=float(row["_title_norm"] or 1.0),
            is_prefix=bool(row["_is_prefix"]),
        )
        for row in rows
    }
