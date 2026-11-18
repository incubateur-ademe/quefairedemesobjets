"""Review policy of each type_action: the front reads these capabilities and has
no rule of its own for a type. Only the SOURCE policies exist for now."""

from dataclasses import dataclass

from data.models.suggestion import SuggestionAction
from data.revue.errors import RevueApiError

REVISION = "RevisionActeur"
PARENT = "ParentRevisionActeur"


@dataclass(frozen=True)
class ReviewPolicy:
    type_action: str
    # A ligne (tuple of champs) is validated on its own
    has_lines: bool = True
    # « Tout le groupe ou rien »: a ligne can never be refused alone
    can_reject_line: bool = False
    can_reject_group: bool = True
    # Objects whose suggestions the reviewer may correct (never Acteur)
    editable_models: tuple[str, ...] = (REVISION, PARENT)
    shows_parent: bool = True
    # Show the current acteur value next to the suggestion (no acteur for AJOUT)
    shows_acteur_diff: bool = True
    badge: str | None = None

    def describe(self) -> dict:
        return {
            "type_action": self.type_action,
            "has_lines": self.has_lines,
            "can_reject_line": self.can_reject_line,
            "can_reject_group": self.can_reject_group,
            "editable_models": list(self.editable_models),
            "shows_parent": self.shows_parent,
            "shows_acteur_diff": self.shows_acteur_diff,
            "badge": self.badge,
        }


SOURCE_MODIFICATION = ReviewPolicy(SuggestionAction.SOURCE_MODIFICATION.value)
# A SUPPRESSION is a MODIFICATION whose only ligne is the `statut` field
SOURCE_SUPPRESSION = ReviewPolicy(SuggestionAction.SOURCE_SUPPRESSION.value)
# A new acteur: no current value to compare, no parent yet
SOURCE_AJOUT = ReviewPolicy(
    SuggestionAction.SOURCE_AJOUT.value,
    editable_models=(REVISION,),
    shows_parent=False,
    shows_acteur_diff=False,
    badge="Nouvel acteur",
)

POLICIES = {
    policy.type_action: policy
    for policy in (SOURCE_AJOUT, SOURCE_MODIFICATION, SOURCE_SUPPRESSION)
}


def get_policy(type_action: str) -> ReviewPolicy:
    try:
        return POLICIES[type_action]
    except KeyError as e:
        raise RevueApiError(
            404, "no_policy", f"Pas de politique de revue pour « {type_action} »"
        ) from e
