"""Serialization of the groupes of a cohorte and of their « lignes de suggestion ».

A ligne is, for a groupe, the set of SuggestionUnitaire sharing the same tuple of
`champs`, whatever their `suggestion_modele` (Acteur, RevisionActeur,
ParentRevisionActeur). Its statut is derived: the groupe statut once the groupe
is not AVALIDER anymore, otherwise ATRAITER when all its SU are validated.
"""

from collections import defaultdict
from collections.abc import Iterable

from django.contrib.admin.utils import quote
from django.db.models import Count, Prefetch, QuerySet
from django.urls import reverse

from data.models.suggestion import (
    SuggestionGroupe,
    SuggestionStatut,
    SuggestionUnitaire,
)
from data.models.suggestions.source import SuggestionSourceModel
from data.revue.policies import PARENT, REVISION, ReviewPolicy
from qfdmo.models.acteur import RevisionActeur

ACTEUR = "Acteur"
NOT_REPORTABLE = {
    REVISION: set(SuggestionSourceModel.get_not_reportable_on_revision_fields()),
    PARENT: set(SuggestionSourceModel.get_not_reportable_on_parent_fields()),
}
NOT_EDITABLE = set(SuggestionSourceModel.get_not_editable_fields())
ORDERED_FIELDS = SuggestionSourceModel.get_ordered_fields()
IDENTITY_FIELDS = ["identifiant_unique", "identifiant_externe", "nom", "ville"]


def ligne_key(groupe_id: int, champs: Iterable[str]) -> str:
    return f"{groupe_id}:{','.join(champs)}"


def parse_ligne_key(key: str) -> tuple[int, list[str]]:
    groupe_id, _, champs = key.partition(":")
    return int(groupe_id), champs.split(",") if champs else []


def ordered_champs(champs_list: Iterable[tuple[str, ...]]) -> list[tuple[str, ...]]:
    """Lignes in the order of the admin (latitude/longitude grouped), unknown last."""
    order = {fields: index for index, fields in enumerate(ORDERED_FIELDS)}
    return sorted(set(champs_list), key=lambda c: (order.get(c, len(order)), c))


def groupes_queryset() -> QuerySet[SuggestionGroupe]:
    """Groupes with everything their serialization needs."""
    return SuggestionGroupe.objects.select_related(
        "decision_par",
        "suggestion_cohorte",
        # LEFT JOIN: a missing row (FK without constraint) gives None
        "acteur",
        "revision_acteur",
        "parent_revision_acteur",
    ).prefetch_related(
        Prefetch(
            "suggestion_unitaires",
            queryset=SuggestionUnitaire.objects.select_related("decision_par").order_by(
                "ordre", "id"
            ),
        )
    )


def _user(user) -> dict | None:
    return {"id": user.id, "username": user.get_username()} if user else None


def _admin_url(name: str, identifiant_unique: str | None) -> str | None:
    if not identifiant_unique:
        return None
    return reverse(f"admin:qfdmo_{name}_change", args=[quote(identifiant_unique)])


def _values(instance, champs: list[str]) -> dict[str, str]:
    model = SuggestionSourceModel.from_acteur(instance, fields_to_include=champs)
    return {champ: getattr(model, champ, None) or "" for champ in champs}


class _GroupeContext:
    """Objects of a groupe, loaded once for all its lignes."""

    def __init__(self, groupe: SuggestionGroupe, nb_enfants: dict[str, int]):
        self.groupe = groupe
        self.sus = list(groupe.suggestion_unitaires.all())
        self.acteur = groupe.get_acteur_or_none()
        self.revision = groupe.get_revision_acteur_or_none()
        self.parent = groupe.get_parent_revision_acteur_or_none()
        self.nb_enfants = nb_enfants
        champs = sorted({champ for su in self.sus for champ in su.champs})
        self.acteur_values = _values(self.acteur, champs) if self.acteur else None
        self.revision_values = _values(self.revision, champs) if self.revision else None
        self.parent_values = _values(self.parent, champs) if self.parent else None

    def sus_of(self, champs: tuple[str, ...]) -> list[SuggestionUnitaire]:
        return [su for su in self.sus if tuple(su.champs) == champs]

    def suggested(self, modele: str, champs: list[str]) -> str | None:
        """Value suggested by the source (SU Acteur) for a champ."""
        for su in self.sus:
            if su.suggestion_modele == modele and champs[0] in su.champs:
                return su.valeurs[su.champs.index(champs[0])]
        return None


def _cell(actuel: dict | None, su: SuggestionUnitaire | None, empty: str) -> dict:
    propose = dict(zip(su.champs, su.valeurs)) if su else None
    return {
        "actuel": actuel,
        "propose": propose,
        "etat": "valeur" if actuel is not None or propose is not None else empty,
    }


def ligne_statut(groupe_statut: str, sus: list[SuggestionUnitaire]) -> str:
    if groupe_statut != SuggestionStatut.AVALIDER:
        return groupe_statut
    if sus and all(su.statut == SuggestionStatut.ATRAITER for su in sus):
        return SuggestionStatut.ATRAITER
    return SuggestionStatut.AVALIDER


def _serialize_ligne(
    context: _GroupeContext, champs: tuple[str, ...], policy: ReviewPolicy
) -> dict:
    groupe = context.groupe
    sus = context.sus_of(champs)
    by_modele = {su.suggestion_modele: su for su in sus}
    statut = ligne_statut(groupe.statut, sus)
    decided = max(
        (su for su in sus if su.decision_le),
        key=lambda su: su.decision_le,
        default=None,
    )
    pick = lambda values: (  # noqa: E731
        {champ: values.get(champ, "") for champ in champs}
        if values is not None
        else None
    )

    actionable = groupe.statut == SuggestionStatut.AVALIDER
    ligne_open = actionable and statut == SuggestionStatut.AVALIDER

    def reportable(modele: str) -> bool:
        """The suggestion of the source may be copied to `modele`, like in the
        admin: only the fields not reportable on `modele` are refused."""
        if modele not in policy.editable_models or not ligne_open:
            return False
        if modele == PARENT and not groupe.parent_revision_acteur_id:
            return False
        return not any(champ in NOT_REPORTABLE[modele] for champ in champs)

    def editable(modele: str) -> bool:
        """A value may also be typed: not for the fields with specific values."""
        return reportable(modele) and not any(champ in NOT_EDITABLE for champ in champs)

    has_parent = bool(groupe.parent_revision_acteur_id) and policy.shows_parent
    return {
        "key": ligne_key(groupe.id, champs),
        "champs": list(champs),
        "statut": statut,
        "decision_par": _user(decided.decision_par) if decided else None,
        "decision_le": decided.decision_le if decided else None,
        "acteur": _cell(
            pick(context.acteur_values) if policy.shows_acteur_diff else None,
            by_modele.get(ACTEUR),
            "vide",
        ),
        "correction": _cell(
            pick(context.revision_values),
            by_modele.get(REVISION),
            "pas_de_correction",
        ),
        "parent": (
            _cell(pick(context.parent_values), by_modele.get(PARENT), "vide")
            if has_parent
            else None
        ),
        "capacites": {
            "valider": ligne_open,
            "remettre_a_valider": statut == SuggestionStatut.ATRAITER
            and groupe.statut in (SuggestionStatut.AVALIDER, SuggestionStatut.ATRAITER),
            "remettre_groupe_a_valider": groupe.statut == SuggestionStatut.REJETEE,
            "corriger_correction": editable(REVISION),
            "corriger_parent": has_parent and editable(PARENT),
            "reporter_correction": reportable(REVISION) and ACTEUR in by_modele,
            "reporter_parent": has_parent
            and reportable(PARENT)
            and ACTEUR in by_modele,
            # A reported value may be removed, even when it cannot be typed
            "supprimer_correction": reportable(REVISION) and REVISION in by_modele,
            "supprimer_parent": has_parent
            and reportable(PARENT)
            and PARENT in by_modele,
        },
    }


def _identity(context: _GroupeContext) -> dict:
    """Identity of the acteur: from the DB, or suggested by the source (AJOUT)."""
    groupe = context.groupe
    values = {
        champ: (getattr(context.acteur, champ, None) if context.acteur else None)
        or context.suggested(ACTEUR, [champ])
        or ""
        for champ in IDENTITY_FIELDS
    }
    identifiant_unique = values["identifiant_unique"] or groupe.acteur_id or ""
    return {
        **values,
        "identifiant_unique": identifiant_unique,
        "admin_urls": {
            "importe": _admin_url("acteur", context.acteur and groupe.acteur_id),
            "affiche": _admin_url(
                "displayedacteur",
                groupe.parent_revision_acteur_id
                or groupe.revision_acteur_id
                or (context.acteur and groupe.acteur_id),
            ),
            "corrige": _admin_url(
                "revisionacteur", context.revision and groupe.revision_acteur_id
            ),
            "parent": _admin_url(
                "revisionacteur", context.parent and groupe.parent_revision_acteur_id
            ),
        },
    }


def serialize_groupe(
    groupe: SuggestionGroupe,
    policy: ReviewPolicy,
    nb_enfants: dict[str, int] | None = None,
) -> dict:
    if nb_enfants is None:
        nb_enfants = count_enfants([groupe])
    context = _GroupeContext(groupe, nb_enfants)
    lignes = [
        _serialize_ligne(context, champs, policy)
        for champs in ordered_champs(tuple(su.champs) for su in context.sus)
    ]
    actionable = groupe.statut == SuggestionStatut.AVALIDER
    parent = None
    if context.parent and policy.shows_parent:
        parent = {
            "identifiant_unique": context.parent.identifiant_unique,
            "nom": context.parent.nom,
            "nb_enfants": nb_enfants.get(context.parent.identifiant_unique, 0),
        }
    return {
        "id": groupe.id,
        "statut": groupe.statut,
        "modifie_le": groupe.modifie_le,
        "decision_par": _user(groupe.decision_par),
        "decision_le": groupe.decision_le,
        "acteur": _identity(context),
        "is_new": policy.badge is not None and context.acteur is None,
        "has_correction": context.revision is not None,
        "parent": parent,
        "lignes": lignes,
        "lignes_validees": sum(
            ligne["statut"] == SuggestionStatut.ATRAITER for ligne in lignes
        ),
        "lignes_total": len(lignes),
        "capacites": {
            "valider": actionable,
            "refuser": actionable and policy.can_reject_group,
            # A decided groupe, or a groupe to validate having validated lignes
            "remettre_a_valider": groupe.statut
            in (SuggestionStatut.ATRAITER, SuggestionStatut.REJETEE)
            or (
                actionable
                and any(
                    ligne["statut"] == SuggestionStatut.ATRAITER for ligne in lignes
                )
            ),
            "reporter_correction": any(
                ligne["capacites"]["reporter_correction"] for ligne in lignes
            ),
            "reporter_parent": any(
                ligne["capacites"]["reporter_parent"] for ligne in lignes
            ),
        },
    }


def count_enfants(groupes: Iterable[SuggestionGroupe]) -> dict[str, int]:
    parent_ids = {g.parent_revision_acteur_id for g in groupes} - {None}
    if not parent_ids:
        return {}
    return dict(
        RevisionActeur.objects.filter(parent_id__in=parent_ids)
        .values("parent_id")
        .annotate(n=Count("pk"))
        .values_list("parent_id", "n")
    )


def serialize_groupes(groupes: list[SuggestionGroupe], policy: ReviewPolicy) -> list:
    nb_enfants = count_enfants(groupes)
    return [serialize_groupe(groupe, policy, nb_enfants) for groupe in groupes]


def lignes_of(groupe: SuggestionGroupe) -> dict[tuple[str, ...], list]:
    """SuggestionUnitaire of the groupe by ligne (tuple of champs)."""
    lignes = defaultdict(list)
    for su in groupe.suggestion_unitaires.all():
        lignes[tuple(su.champs)].append(su)
    return lignes
