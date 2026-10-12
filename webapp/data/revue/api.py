"""API of the SOURCE suggestions review screen, mounted on /api/suggestions/.

Handlers stay thin: business rules live in the other modules of data.revue."""

from django.http import HttpRequest, HttpResponse
from ninja import Query, Router

from data.revue import cohortes, exports, revue, services
from data.revue.auth import SuperuserSessionAuth
from data.revue.filters import parse_filter
from data.revue.lignes import groupes_queryset, serialize_groupes
from data.revue.pagination import paginate
from data.revue.policies import get_policy
from data.revue.schemas import (
    CohorteDetailOut,
    CohortePageOut,
    CohortesQuery,
    ErrorOut,
    FilterMetaOut,
    GroupeDecisionIn,
    GroupeOut,
    GroupePageOut,
    GroupesQuery,
    LignesDecisionIn,
    LogPageOut,
    LogsExportQuery,
    LogsQuery,
    PropositionDeleteQuery,
    PropositionIn,
    ReportIn,
    StatsOut,
    StatsQuery,
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


@router.get(
    "/cohortes/{cohorte_id}/logs/export",
    openapi_extra={
        "responses": {
            200: {
                "description": "Logs de la cohorte au format Excel",
                "content": {exports.XLSX_CONTENT_TYPE: {}},
            }
        }
    },
)
def export_cohorte_logs(
    request: HttpRequest, cohorte_id: int, query: Query[LogsExportQuery]
):
    """Excel export of the logs of a cohorte (same order and level filter)."""
    cohorte = cohortes.get_source_cohorte(cohorte_id)
    response = HttpResponse(
        exports.logs_xlsx(cohorte, query.niveau), content_type=exports.XLSX_CONTENT_TYPE
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{exports.export_filename(cohorte)}"'
    )
    return response


# --- Review of a cohorte ---

WRITE_RESPONSES = {200: GroupeOut, 404: ErrorOut, 409: ErrorOut, 422: ErrorOut}


@router.get("/cohortes/{cohorte_id}", response={200: CohorteDetailOut, 404: ErrorOut})
def cohorte_detail(request: HttpRequest, cohorte_id: int):
    cohorte = cohortes.source_cohortes().filter(id=cohorte_id).first()
    if cohorte is None:
        cohortes.get_source_cohorte(cohorte_id)  # 404
    cohortes.attach_counts([cohorte])
    cohorte.policy = get_policy(cohorte.type_action).describe()
    return cohorte


@router.get("/cohortes/{cohorte_id}/revue/filtres", response=FilterMetaOut)
def review_filters(request: HttpRequest, cohorte_id: int):
    cohorte = cohortes.get_source_cohorte(cohorte_id)
    return {"champs": revue.review_filter_metadata(cohorte)}


@router.get(
    "/cohortes/{cohorte_id}/groupes", response={200: GroupePageOut, 422: ErrorOut}
)
def list_groupes(request: HttpRequest, cohorte_id: int, query: Query[GroupesQuery]):
    cohorte = cohortes.get_source_cohorte(cohorte_id)
    groupes = revue.filtered_groupes(
        cohorte,
        parse_filter(query.filtre),
        revue.parse_tuples(query.tuples),
        query.afficher,
    )
    ids, total = paginate(
        groupes.order_by("id").values_list("id", flat=True),
        query.page,
        query.page_size,
    )
    items = list(groupes_queryset().filter(id__in=ids).order_by("id"))
    return {
        "items": serialize_groupes(items, get_policy(cohorte.type_action)),
        "total": total,
        "page": query.page,
        "page_size": query.page_size,
    }


@router.get("/cohortes/{cohorte_id}/stats", response={200: StatsOut, 422: ErrorOut})
def review_stats(request: HttpRequest, cohorte_id: int, query: Query[StatsQuery]):
    cohorte = cohortes.get_source_cohorte(cohorte_id)
    return revue.stats(
        cohorte,
        query.vue,
        parse_filter(query.filtre),
        revue.parse_tuples(query.tuples),
        query.afficher,
    )


@router.post("/groupes/{groupe_id}/decision", response=WRITE_RESPONSES)
def groupe_decision(request: HttpRequest, groupe_id: int, payload: GroupeDecisionIn):
    return services.decide_groupe(
        groupe_id, payload.action, request.auth, payload.expected_modifie_le
    )


@router.post("/groupes/{groupe_id}/lignes/decision", response=WRITE_RESPONSES)
def lignes_decision(request: HttpRequest, groupe_id: int, payload: LignesDecisionIn):
    return services.decide_lignes(
        groupe_id,
        payload.champs,
        payload.action,
        request.auth,
        payload.expected_modifie_le,
    )


@router.put("/groupes/{groupe_id}/propositions", response=WRITE_RESPONSES)
def upsert_proposition(request: HttpRequest, groupe_id: int, payload: PropositionIn):
    return services.upsert_proposition(
        groupe_id,
        payload.suggestion_modele,
        payload.champs,
        payload.valeurs,
        payload.expected_modifie_le,
    )


@router.delete("/groupes/{groupe_id}/propositions", response=WRITE_RESPONSES)
def delete_proposition(
    request: HttpRequest, groupe_id: int, query: Query[PropositionDeleteQuery]
):
    return services.delete_proposition(
        groupe_id, query.suggestion_modele, query.champs, query.expected_modifie_le
    )


@router.post("/groupes/{groupe_id}/report", response=WRITE_RESPONSES)
def report(request: HttpRequest, groupe_id: int, payload: ReportIn):
    return services.report(
        groupe_id, payload.cible, payload.champs, payload.expected_modifie_le
    )
