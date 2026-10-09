"""API of the SOURCE suggestions review screen, mounted on /api/suggestions/.

Handlers stay thin: business rules live in the other modules of data.revue."""

from django.http import HttpRequest
from ninja import Query, Router

from data.revue import cohortes
from data.revue.auth import SuperuserSessionAuth
from data.revue.filters import parse_filter
from data.revue.schemas import (
    CohortePageOut,
    CohortesQuery,
    ErrorOut,
    FilterMetaOut,
    LogPageOut,
    LogsQuery,
    UserOut,
)

router = Router(auth=SuperuserSessionAuth(), tags=["Revue suggestions"])


@router.get("/me", response=UserOut)
def me(request: HttpRequest):
    return request.auth


@router.get("/cohortes", response={200: CohortePageOut, 422: ErrorOut})
def list_cohortes(request: HttpRequest, query: Query[CohortesQuery]):
    return cohortes.cohortes_page(
        filtre=parse_filter(query.filtre),
        type_action=query.type_action,
        statut=query.statut,
        cree_apres=query.cree_apres,
        cree_avant=query.cree_avant,
        tri=query.tri,
        page=query.page,
        page_size=query.page_size,
    )


@router.get("/cohortes/filtres", response=FilterMetaOut)
def cohortes_filters(request: HttpRequest):
    return {"champs": cohortes.cohortes_filter_metadata()}


@router.get("/cohortes/{cohorte_id}/logs", response=LogPageOut)
def cohorte_logs(request: HttpRequest, cohorte_id: int, query: Query[LogsQuery]):
    cohorte = cohortes.get_source_cohorte(cohorte_id)
    return cohortes.logs_page(cohorte, query.niveau, query.page, query.page_size)
