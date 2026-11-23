"""Serialization of the groupes of a cohorte and of their « lignes de suggestion ».

A ligne is, for a groupe, the set of SuggestionUnitaire sharing the same tuple of
`champs`, whatever their `suggestion_modele` (Acteur, RevisionActeur,
ParentRevisionActeur). When the groupe gathers several acteurs
(`ReviewPolicy.lignes_par_acteur`), a ligne is also restricted to one acteur, its
« cible »: the acteur of its SU (`cible_of`).

Its statut is derived from its SU and its groupe: refused when all its SU are
refused (or its groupe is), otherwise the groupe statut once the groupe is not
AVALIDER anymore, otherwise ATRAITER when all its SU are validated.
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
from data.revue.choix import EDITABLE
from data.revue.policies import PARENT, REVISION, ReviewPolicy
from qfdmo.models.acteur import Acteur, RevisionActeur

ACTEUR = "Acteur"
NOT_REPORTABLE = {
    REVISION: set(SuggestionSourceModel.get_not_reportable_on_revision_fields()),
    PARENT: set(SuggestionSourceModel.get_not_reportable_on_parent_fields()),
}
# The codes and services are edited with selects in this screen
# (data.revue.choix), unlike in the admin
NOT_EDITABLE = set(SuggestionSourceModel.get_not_editable_fields()) - EDITABLE
ORDERED_FIELDS = SuggestionSourceModel.get_ordered_fields()
IDENTITY_FIELDS = ["identifiant_unique", "identifiant_externe", "nom", "ville"]


def cible_of(su: SuggestionUnitaire) -> str:
    """Acteur targeted by a SU (same order as `revue.CIBLE` in SQL)."""
    return su.acteur_id or su.revision_acteur_id or su.parent_revision_acteur_id or ""


def ligne_cible(su: SuggestionUnitaire, policy: ReviewPolicy) -> str | None:
    """Cible of the ligne of a SU: None when the groupe is a single acteur."""
    return cible_of(su) if policy.lignes_par_acteur else None


def ligne_key(groupe_id: int, champs: Iterable[str], cible: str | None = None) -> str:
    """`groupe:champs`, or `groupe:cible:champs` for the lignes par acteur."""
    champs = ",".join(champs)
    return f"{groupe_id}:{champs}" if cible is None else f"{groupe_id}:{cible}:{champs}"


def parse_ligne_key(key: str) -> tuple[int, str | None, list[str]]:
    """(groupe id, cible or None, champs). The champs never contain « : »."""
    groupe_id, _, rest = key.partition(":")
    cible, separator, champs = rest.rpartition(":")
    return (
        int(groupe_id),
        cible if separator else None,
        champs.split(",") if champs else [],
    )


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


def field_values(instance, champs: list[str]) -> dict[str, str]:
    model = SuggestionSourceModel.from_acteur(instance, fields_to_include=champs)
    return {champ: getattr(model, champ, None) or "" for champ in champs}


class _Objets:
    """Acteur, correction and parent of a ligne, with their current values."""

    def __init__(self, acteur, revision, parent, champs: list[str]):
        self.acteur = acteur
        self.revision = revision
        self.parent = parent
        self.acteur_values = field_values(acteur, champs) if acteur else None
        self.revision_values = field_values(revision, champs) if revision else None
        self.parent_values = field_values(parent, champs) if parent else None


class _GroupeContext:
    """Objects of a groupe, loaded once for all its lignes."""

    def __init__(
        self,
        groupe: SuggestionGroupe,
        nb_enfants: dict[str, int],
        policy: ReviewPolicy,
    ):
        self.groupe = groupe
        self.policy = policy
        self.sus = list(groupe.suggestion_unitaires.all())
        self.acteur = groupe.get_acteur_or_none()
        self.revision = groupe.get_revision_acteur_or_none()
        self.parent = groupe.get_parent_revision_acteur_or_none()
        self.nb_enfants = nb_enfants
        champs = sorted({champ for su in self.sus for champ in su.champs})
        self.objets = _Objets(self.acteur, self.revision, self.parent, champs)
        self.objets_par_cible: dict[str, _Objets] = {}
        if policy.lignes_par_acteur:
            self._load_cibles(champs)

    def _load_cibles(self, champs: list[str]):
        """One acteur per ligne: its Acteur and RevisionActeur, loaded at once.
        A SU on the parent targets an acteur which is itself a parent."""
        cibles = {cible_of(su) for su in self.sus} - {""}
        acteurs = Acteur.objects.in_bulk(list(cibles))
        revisions = RevisionActeur.objects.in_bulk(list(cibles))
        parents = {cible_of(su) for su in self.sus if su.suggestion_modele == PARENT}
        for cible in cibles:
            revision = revisions.get(cible)
            is_parent = cible in parents
            self.objets_par_cible[cible] = _Objets(
                acteurs.get(cible),
                None if is_parent else revision,
                revision if is_parent else None,
                champs,
            )

    def objets_of(self, cible: str | None) -> _Objets:
        if cible is None:
            return self.objets
        return self.objets_par_cible.get(cible) or _Objets(None, None, None, [])

    def lignes(self) -> list[tuple[str | None, tuple[str, ...]]]:
        """(cible, champs) of the lignes: by acteur, then in the admin order."""
        cles = {(ligne_cible(su, self.policy), tuple(su.champs)) for su in self.sus}
        order = {fields: index for index, fields in enumerate(ORDERED_FIELDS)}
        return sorted(
            cles,
            key=lambda c: (c[0] or "", order.get(c[1], len(order)), c[1]),
        )

    def sus_of(
        self, champs: tuple[str, ...], cible: str | None = None
    ) -> list[SuggestionUnitaire]:
        return [
            su
            for su in self.sus
            if tuple(su.champs) == champs and ligne_cible(su, self.policy) == cible
        ]

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
    if groupe_statut == SuggestionStatut.REJETEE or (
        sus and all(su.statut == SuggestionStatut.REJETEE for su in sus)
    ):
        return SuggestionStatut.REJETEE
    if groupe_statut != SuggestionStatut.AVALIDER:
        return groupe_statut
    if sus and all(su.statut == SuggestionStatut.ATRAITER for su in sus):
        return SuggestionStatut.ATRAITER
    return SuggestionStatut.AVALIDER


def _serialize_ligne(
    context: _GroupeContext,
    champs: tuple[str, ...],
    policy: ReviewPolicy,
    cible: str | None = None,
) -> dict:
    groupe = context.groupe
    sus = context.sus_of(champs, cible)
    objets = context.objets_of(cible)
    parent_id = (
        objets.parent.identifiant_unique
        if cible is not None and objets.parent
        else groupe.parent_revision_acteur_id
    )
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
        if modele == PARENT and not parent_id:
            return False
        return not any(champ in NOT_REPORTABLE[modele] for champ in champs)

    def editable(modele: str) -> bool:
        """A value may also be typed: not for the fields with specific values."""
        return reportable(modele) and not any(champ in NOT_EDITABLE for champ in champs)

    has_parent = bool(parent_id) and policy.shows_parent
    # A refused ligne goes back to validate on its own when lignes are refused
    # one by one, otherwise with its whole groupe
    reopenable_lignes = (
        (SuggestionStatut.ATRAITER, SuggestionStatut.REJETEE)
        if policy.can_reject_line
        else (SuggestionStatut.ATRAITER,)
    )
    reopenable_groupe = (
        (SuggestionStatut.AVALIDER, SuggestionStatut.ATRAITER, SuggestionStatut.REJETEE)
        if policy.can_reject_line
        else (SuggestionStatut.AVALIDER, SuggestionStatut.ATRAITER)
    )
    return {
        "key": ligne_key(groupe.id, champs, cible),
        "champs": list(champs),
        "cible": _cible_identity(cible, objets, sus) if cible is not None else None,
        "statut": statut,
        "decision_par": _user(decided.decision_par) if decided else None,
        "decision_le": decided.decision_le if decided else None,
        "acteur": _cell(
            pick(objets.acteur_values) if policy.shows_acteur_diff else None,
            by_modele.get(ACTEUR),
            "vide",
        ),
        "correction": _cell(
            pick(objets.revision_values),
            by_modele.get(REVISION),
            "pas_de_correction",
        ),
        "parent": (
            _cell(pick(objets.parent_values), by_modele.get(PARENT), "vide")
            if has_parent
            else None
        ),
        "capacites": {
            "valider": ligne_open,
            "refuser": ligne_open and policy.can_reject_line,
            "remettre_a_valider": statut in reopenable_lignes
            and groupe.statut in reopenable_groupe,
            "remettre_groupe_a_valider": groupe.statut == SuggestionStatut.REJETEE
            and not policy.can_reject_line,
            "corriger_correction": editable(REVISION),
            "corriger_parent": has_parent and editable(PARENT),
            "reporter_correction": reportable(REVISION) and ACTEUR in by_modele,
            "reporter_parent": has_parent
            and reportable(PARENT)
            and ACTEUR in by_modele,
            # Correction with the value of the acteur, cancelling the suggestion
            "restaurer_correction": policy.can_restore
            and reportable(REVISION)
            and ACTEUR in by_modele
            and objets.acteur is not None,
            # A reported value may be removed, even when it cannot be typed
            "supprimer_correction": reportable(REVISION) and REVISION in by_modele,
            "supprimer_parent": has_parent
            and reportable(PARENT)
            and PARENT in by_modele,
        },
    }


def _cible_identity(cible: str, objets: _Objets, sus: list[SuggestionUnitaire]) -> dict:
    """Acteur of a ligne par acteur: its identity and its admin pages."""
    instance = objets.revision or objets.parent or objets.acteur
    modele = sus[0].suggestion_modele if sus else ""
    return {
        "identifiant_unique": cible,
        "nom": (getattr(instance, "nom", None) or getattr(objets.acteur, "nom", None))
        or "",
        "ville": (
            getattr(instance, "ville", None) or getattr(objets.acteur, "ville", None)
        )
        or "",
        "suggestion_modele": modele,
        "admin_urls": {
            "importe": _admin_url("acteur", objets.acteur and cible),
            "affiche": _admin_url("displayedacteur", cible),
            "corrige": _admin_url("revisionacteur", objets.revision and cible),
            "parent": _admin_url("revisionacteur", objets.parent and cible),
        },
    }


def _libelle(groupe: SuggestionGroupe) -> str:
    """Label of a groupe of several acteurs: its contexte (ex: suggested value)."""
    contexte = groupe.contexte if isinstance(groupe.contexte, dict) else {}
    return " · ".join(f"{key} : {value}" for key, value in contexte.items())


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
    context = _GroupeContext(groupe, nb_enfants, policy)
    lignes = [
        _serialize_ligne(context, champs, policy, cible)
        for cible, champs in context.lignes()
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
        "libelle": _libelle(groupe) if policy.lignes_par_acteur else None,
        "is_new": policy.badge is not None and context.acteur is None,
        "has_correction": context.revision is not None,
        "parent": parent,
        "lignes": lignes,
        "lignes_validees": sum(
            ligne["statut"] == SuggestionStatut.ATRAITER for ligne in lignes
        ),
        "lignes_refusees": sum(
            ligne["statut"] == SuggestionStatut.REJETEE for ligne in lignes
        ),
        "lignes_total": len(lignes),
        "capacites": {
            "valider": actionable,
            "refuser": actionable and policy.can_reject_group,
            # A decided groupe, or a groupe to validate having decided lignes
            "remettre_a_valider": groupe.statut
            in (SuggestionStatut.ATRAITER, SuggestionStatut.REJETEE)
            or (
                actionable
                and any(
                    ligne["statut"]
                    in (SuggestionStatut.ATRAITER, SuggestionStatut.REJETEE)
                    for ligne in lignes
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


def sus_by_key(groupe: SuggestionGroupe, policy: ReviewPolicy) -> dict[str, list]:
    """SuggestionUnitaire of the groupe by ligne key."""
    lignes = defaultdict(list)
    for su in groupe.suggestion_unitaires.all():
        lignes[ligne_key(groupe.id, su.champs, ligne_cible(su, policy))].append(su)
    return lignes
