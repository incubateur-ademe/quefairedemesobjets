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
