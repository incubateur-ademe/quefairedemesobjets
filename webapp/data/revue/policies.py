"""Review policy of each type_action: the front reads these capabilities and has
no rule of its own for a type. A cohorte is reviewable in this screen only when
its type_action has a policy (`REVUE_TYPE_ACTIONS`)."""

from dataclasses import dataclass

from data.models.suggestion import SuggestionAction
from data.revue.errors import RevueApiError

REVISION = "RevisionActeur"
PARENT = "ParentRevisionActeur"
LOCALISATION = "localisation"
ANNUAIRE = "annuaire"


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
    # The comparison table has the parent columns (⏩ and Parent)
    colonne_parent: bool = True
    # Show the current acteur value next to the suggestion (no acteur for AJOUT)
    shows_acteur_diff: bool = True
    # The correction may take back the current value of the acteur
    can_restore: bool = True
    # The groupe gathers several acteurs (1 SuggestionUnitaire per acteur, the
    # acteur being on the SU, not on the groupe): a ligne is (acteur, champs)
    lignes_by_acteur: bool = False
    # Tabs of the modal of a groupe (and their buttons on the groupe header)
    tabs: tuple[str, ...] = (LOCALISATION, ANNUAIRE)
    # Identifiers shown with the acteur of a ligne par acteur (ex: its SIREN
    # when a SIRET is proposed)
    identifiants_target: tuple[str, ...] = ()
    badge: str | None = None

    def describe(self) -> dict:
        return {
            "type_action": self.type_action,
            "has_lines": self.has_lines,
            "can_reject_line": self.can_reject_line,
            "can_reject_group": self.can_reject_group,
            "editable_models": list(self.editable_models),
            "shows_parent": self.shows_parent,
            "colonne_parent": self.colonne_parent,
            "shows_acteur_diff": self.shows_acteur_diff,
            "can_restore": self.can_restore,
            "lignes_by_acteur": self.lignes_by_acteur,
            "tabs": list(self.tabs),
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

# Closed SIRET (enrich DAG): 1 groupe per acteur, 1 SuggestionUnitaire per field
# suggested on the correction (RevisionActeur); no suggestion on the Acteur, so
# nothing to report, but the correction and the parent may be edited
ENRICH_ACTEURS_CLOSED = ReviewPolicy(
    SuggestionAction.ENRICH_ACTEURS_CLOSED.value, tabs=()
)
# RGPD anonymisation (enrich DAG): 1 groupe per acteur, the anonymised values
# overwrite the Acteur and its RevisionActeur if it exists. The correction may be
# edited, to reactivate the acteur with non personal information; restoring the
# value of the acteur would bring back the personal data
ENRICH_ACTEURS_RGPD = ReviewPolicy(
    SuggestionAction.ENRICH_ACTEURS_RGPD.value,
    editable_models=(REVISION,),
    shows_parent=False,
    can_restore=False,
    tabs=(),
)

# Other enrich DAGs: 1 groupe per suggested value (villes, codes postaux, SIRET,
# SIREN) or per acteur (lien de succession), the acteur being on each
# SuggestionUnitaire. Each ligne is validated or refused on its own: the groupe
# stays to validate while a ligne is to validate, and only its validated lignes
# are applied. No correction for now: nothing to edit, report or restore. No
# localisation; the Annuaire Entreprises only for the SIRET and SIREN cohortes.
# No parent column for the codes postaux (DAG enrich_acteurs_normalize_codepostal).
ENRICH_PAR_LIGNE = tuple(
    ReviewPolicy(
        type_action.value,
        can_reject_line=True,
        lignes_by_acteur=True,
        editable_models=(),
        can_restore=False,
        tabs=tabs,
        shows_parent=parent,
        colonne_parent=parent,
        identifiants_target=identifiants,
    )
    for type_action, tabs, parent, identifiants in (
        (SuggestionAction.ENRICH_ACTEURS_VILLES_TYPO, (), True, ()),
        (SuggestionAction.ENRICH_ACTEURS_VILLES_NEW, (), True, ()),
        (SuggestionAction.ENRICH_ACTEURS_CP_TYPO, (), False, ()),
        (SuggestionAction.ENRICH_REVISION_ACTEURS_CP_TYPO, (), False, ()),
        # SIRET proposed from the known SIREN, and vice versa
        (SuggestionAction.ENRICH_ACTEURS_SIRET, (ANNUAIRE,), True, ("siren",)),
        (SuggestionAction.ENRICH_ACTEURS_SIREN, (ANNUAIRE,), True, ("siret",)),
        (SuggestionAction.ENRICH_ACTEURS_LIEN_SUCCESSION, (), True, ()),
    )
)

POLICIES = {
    policy.type_action: policy
    for policy in (
        SOURCE_AJOUT,
        SOURCE_MODIFICATION,
        SOURCE_SUPPRESSION,
        ENRICH_ACTEURS_CLOSED,
        ENRICH_ACTEURS_RGPD,
        *ENRICH_PAR_LIGNE,
    )
}

# type_action of the cohortes listed and reviewed by this screen
REVUE_TYPE_ACTIONS = list(POLICIES)


def get_policy(type_action: str) -> ReviewPolicy:
    try:
        return POLICIES[type_action]
    except KeyError as e:
        raise RevueApiError(
            404, "no_policy", f"Pas de politique de revue pour « {type_action} »"
        ) from e
