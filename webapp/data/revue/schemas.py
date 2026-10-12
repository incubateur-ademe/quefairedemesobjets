from datetime import date, datetime
from typing import Any, Literal

from ninja import Field, Schema


class UserOut(Schema):
    id: int
    username: str


class ErrorOut(Schema):
    code: str
    detail: str
    errors: dict[str, list[str]] | None = None
    current: dict[str, Any] | None = None


# --- Filters ---


class ChoiceOut(Schema):
    value: str
    label: str


class FilterFieldOut(Schema):
    key: str
    label: str
    famille: Literal["cohorte", "groupe", "ligne"]
    type: Literal["text", "number", "date", "bool", "choice", "user"]
    operateurs: list[str]
    choix: list[ChoiceOut] | None = None


class FilterMetaOut(Schema):
    champs: list[FilterFieldOut]


# --- Cohortes ---


class CompteursOut(Schema):
    AVALIDER: int
    ATRAITER: int
    REJETEE: int
    ENCOURS: int
    SUCCES: int
    ERREUR: int


class LogsCountOut(Schema):
    ERROR: int
    WARNING: int
    INFO: int


class CohorteOut(Schema):
    id: int
    identifiant_action: str
    identifiant_execution: str
    execution_datetime: str
    type_action: str
    type_action_label: str = Field(..., alias="get_type_action_display")
    statut: str
    cree_le: datetime
    metadata: Any = None
    total_groupes: int
    compteurs: CompteursOut
    logs: LogsCountOut


class CohortePageOut(Schema):
    items: list[CohorteOut]
    total: int
    page: int
    page_size: int


class CohortesQuery(Schema):
    filtre: str | None = None
    type_action: list[str] = []
    statut: list[str] = []
    cree_apres: date | None = None
    cree_avant: date | None = None
    tri: str | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)


# --- Logs ---


class LogOut(Schema):
    id: int
    niveau: str = Field(..., alias="niveau_de_log")
    message: str
    fonction_de_transformation: str
    identifiant_unique: str
    origine_colonnes: list[str] | None
    origine_valeurs: list[str] | None
    destination_colonnes: list[str] | None
    suggestion_groupe_id: int | None
    cree_le: datetime


class LogPageOut(Schema):
    items: list[LogOut]
    total: int
    page: int
    page_size: int


class LogsQuery(Schema):
    niveau: list[str] = []
    page: int = Field(1, ge=1)
    page_size: int = Field(100, ge=1, le=500)


class LogsExportQuery(Schema):
    niveau: list[str] = []


# --- Review of a cohorte ---


class PolicyOut(Schema):
    type_action: str
    has_lines: bool
    can_reject_line: bool
    can_reject_group: bool
    editable_models: list[str]
    shows_parent: bool
    shows_acteur_diff: bool
    badge: str | None


class CohorteDetailOut(CohorteOut):
    policy: PolicyOut


class CellOut(Schema):
    actuel: dict[str, str] | None
    propose: dict[str, str] | None
    etat: Literal["valeur", "vide", "pas_de_correction"]


class LigneCapacitesOut(Schema):
    valider: bool
    remettre_a_valider: bool
    remettre_groupe_a_valider: bool
    corriger_correction: bool
    corriger_parent: bool
    reporter_correction: bool
    reporter_parent: bool
    supprimer_correction: bool
    supprimer_parent: bool


class LigneOut(Schema):
    key: str
    champs: list[str]
    statut: str
    decision_par: UserOut | None
    decision_le: datetime | None
    acteur: CellOut
    correction: CellOut
    parent: CellOut | None
    capacites: LigneCapacitesOut


class AdminUrlsOut(Schema):
    importe: str | None
    affiche: str | None
    corrige: str | None
    parent: str | None


class ActeurIdentiteOut(Schema):
    identifiant_unique: str
    identifiant_externe: str
    nom: str
    ville: str
    admin_urls: AdminUrlsOut


class ParentOut(Schema):
    identifiant_unique: str
    nom: str
    nb_enfants: int


class GroupeCapacitesOut(Schema):
    valider: bool
    refuser: bool
    remettre_a_valider: bool
    reporter_correction: bool
    reporter_parent: bool


class GroupeOut(Schema):
    id: int
    statut: str
    modifie_le: datetime
    decision_par: UserOut | None
    decision_le: datetime | None
    acteur: ActeurIdentiteOut
    is_new: bool
    has_correction: bool
    parent: ParentOut | None
    lignes: list[LigneOut]
    lignes_validees: int
    lignes_total: int
    capacites: GroupeCapacitesOut


class GroupePageOut(Schema):
    items: list[GroupeOut]
    total: int
    page: int
    page_size: int


class TupleCountOut(Schema):
    champs: list[str]
    count: int


class TotauxVuesOut(Schema):
    groupes: int
    lignes: int


class StatsOut(Schema):
    compteurs: CompteursOut
    totaux_vues: TotauxVuesOut
    tuples: list[TupleCountOut]


class RevueQuery(Schema):
    filtre: str | None = None
    tuples: list[str] = Field(
        [], description="Tuples de champs, chacun écrit « champ,champ »"
    )
    afficher: Literal["avalider", "tout"] = "avalider"


class GroupesQuery(RevueQuery):
    page: int = Field(1, ge=1)
    page_size: int = Field(100, ge=1, le=200)


class StatsQuery(RevueQuery):
    vue: Literal["groupes", "lignes"] = "groupes"


# --- Writes ---


class GroupeDecisionIn(Schema):
    action: Literal["validate", "reject", "resubmit"]
    expected_modifie_le: datetime | None = None


class LignesDecisionIn(Schema):
    champs: list[list[str]] = Field(..., min_length=1)
    action: Literal["validate", "resubmit"]
    expected_modifie_le: datetime | None = None


class PropositionIn(Schema):
    suggestion_modele: Literal["RevisionActeur", "ParentRevisionActeur"]
    champs: list[str] = Field(..., min_length=1)
    valeurs: dict[str, str]
    expected_modifie_le: datetime | None = None


class PropositionDeleteQuery(Schema):
    suggestion_modele: Literal["RevisionActeur", "ParentRevisionActeur"]
    champs: list[str] = Field(..., min_length=1)
    expected_modifie_le: datetime | None = None


class ReportIn(Schema):
    cible: Literal["correction", "parent"]
    champs: list[list[str]] | None = Field(
        None, description="Lignes à reporter ; absent = toutes les lignes reportables"
    )
    expected_modifie_le: datetime | None = None


# --- Detail of a groupe (modal) ---


class PointOut(Schema):
    key: Literal["Origin", "Acteur", "RevisionActeur", "ParentRevisionActeur"]
    latitude: float
    longitude: float
    draggable: bool


class LocalisationOut(Schema):
    points: list[PointOut]
    ligne: str | None = Field(
        None, description="Clé de la ligne (latitude, longitude) du groupe"
    )
    creer_correction: bool = Field(
        False,
        description="Pas encore de proposition de localisation sur la correction "
        "(SU latitude/longitude sur RevisionActeur) : en ajouter une",
    )


class IdentifiantOut(Schema):
    source: Literal["corrige", "parent", "correction", "acteur"]
    label: str
    valeur: str
    propose: bool = Field(..., description="Valeur proposée (et non actuelle)")


class AnnuaireOut(Schema):
    siret: list[IdentifiantOut]
    siren: list[IdentifiantOut]


class EntrepriseOut(Schema):
    siren: str
    nom: str
    adresse: str
    activite_code: str
    etat: Literal["actif", "inactif"]


class EtablissementOut(Schema):
    siret: str
    nom: str
    adresse: str
    activite_code: str
    etat: Literal["actif", "ferme"]
    est_siege: bool
    latitude: float | None = None
    longitude: float | None = None


class AnnuaireEntrepriseOut(Schema):
    trouve: bool
    entreprise: EntrepriseOut | None
    etablissement: EtablissementOut | None


class AnnuaireQuery(Schema):
    champ: Literal["siret", "siren"]
    valeur: str


class GroupeDetailOut(GroupeOut):
    localisation: LocalisationOut
    annuaire: AnnuaireOut


# --- View « Lignes » ---


class LigneRefOut(Schema):
    groupe_id: int
    key: str


class LignePageOut(Schema):
    """The lignes of the page are given by reference: each ligne is found in its
    groupe (`groupes`), which is what the writes return and update."""

    items: list[LigneRefOut]
    groupes: list[GroupeOut]
    total: int
    page: int
    page_size: int


class LignesQuery(RevueQuery):
    page: int = Field(1, ge=1)
    page_size: int = Field(500, ge=1, le=1000)


# --- Mass actions ---


class IdsSelectionIn(Schema):
    mode: Literal["ids"]
    ids: list[int | str] = Field(..., max_length=5000)


class FiltreSelectionIn(Schema):
    mode: Literal["filtre"]
    filtre: str | None = None
    tuples: list[str] = []
    afficher: Literal["avalider", "tout"] = "avalider"
    exclus: list[int | str] = Field([], max_length=5000)


class MassSelectionIn(Schema):
    vue: Literal["groupes", "lignes"]
    selection: IdsSelectionIn | FiltreSelectionIn = Field(..., discriminator="mode")


class MassActionIn(MassSelectionIn):
    action: Literal[
        "validate", "reject", "resubmit", "report_correction", "report_parent"
    ]


MassAction = Literal[
    "validate", "reject", "resubmit", "report_correction", "report_parent"
]


class MassPreviewOut(Schema):
    """Number of elements (groupes or lignes) each action would really change."""

    compteurs: dict[MassAction, int]


class MassResultOut(Schema):
    affected: int
    skipped: int


class MassJobOut(Schema):
    job_id: str
    total: int


class JobOut(Schema):
    status: Literal["pending", "running", "done", "error"]
    affected: int | None
