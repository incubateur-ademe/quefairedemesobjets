"""API of the SOURCE suggestions review screen, mounted on /api/suggestions/.

Handlers stay thin: business rules live in the other modules of data.revue."""

from data.models.suggestion import SOURCE_TYPE_ACTIONS, SuggestionCohorte
from data.revue.annuaire import lookup as annuaire_lookup
from data.revue.auth import SuperuserSessionAuth
from data.revue.cohortes import (
    attach_counts,
    cohortes_filter_metadata,
    cohortes_page,
    get_source_cohorte,
    logs_page,
)
from data.revue.detail import serialize_groupe_detail
from data.revue.errors import RevueApiError
from data.revue.exports import XLSX_CONTENT_TYPE, export_filename, logs_xlsx
from data.revue.filters import parse_filter
from data.revue.lignes import groupes_queryset, ligne_key, serialize_groupes
from data.revue.pagination import paginate
from data.revue.policies import get_policy
from data.revue.revue import (
    filtered_groupes,
    parse_tuples,
    review_filter_metadata,
    stats,
)
from data.revue.schemas import (
    AnnuaireEntrepriseOut,
    AnnuaireQuery,
    CohorteDetailOut,
    CohortePageOut,
    CohortesQuery,
    ErrorOut,
    FilterMetaOut,
    GroupeDecisionIn,
    GroupeDetailOut,
    GroupeOut,
    GroupePageOut,
    GroupesQuery,
    LignePageOut,
    LignesDecisionIn,
    LignesQuery,
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
from data.revue.services import decide_groupe, decide_lignes
from data.revue.services import delete_proposition as delete_proposition_service
from data.revue.services import report as report_service
from data.revue.services import upsert_proposition as upsert_proposition_service
from django.http import HttpRequest, HttpResponse
from ninja import Query, Router

router = Router(auth=SuperuserSessionAuth(), tags=["Revue suggestions"])


@router.get("/me", response=UserOut)
def me(request: HttpRequest):
    return request.auth


@router.get("/cohortes", response={200: CohortePageOut, 422: ErrorOut})
def list_cohortes(request: HttpRequest, query: Query[CohortesQuery]):
    return cohortes_page(
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
    return {"champs": cohortes_filter_metadata()}


@router.get("/cohortes/{cohorte_id}/logs", response=LogPageOut)
def cohorte_logs(request: HttpRequest, cohorte_id: int, query: Query[LogsQuery]):
    cohorte = get_source_cohorte(cohorte_id)
    return logs_page(cohorte, query.niveau, query.page, query.page_size)


@router.get(
    "/cohortes/{cohorte_id}/logs/export",
    openapi_extra={
        "responses": {
            200: {
                "description": "Logs de la cohorte au format Excel",
                "content": {XLSX_CONTENT_TYPE: {}},
            }
        }
    },
)
def export_cohorte_logs(
    request: HttpRequest, cohorte_id: int, query: Query[LogsExportQuery]
):
    """Excel export of the logs of a cohorte (same order and level filter)."""
    cohorte = get_source_cohorte(cohorte_id)
    response = HttpResponse(
        logs_xlsx(cohorte, query.niveau), content_type=XLSX_CONTENT_TYPE
    )
    response["Content-Disposition"] = (
        f'attachment; filename="{export_filename(cohorte)}"'
    )
    return response


# --- Review of a cohorte ---

WRITE_RESPONSES = {200: GroupeOut, 404: ErrorOut, 409: ErrorOut, 422: ErrorOut}


@router.get("/cohortes/{cohorte_id}", response={200: CohorteDetailOut, 404: ErrorOut})
def cohorte_detail(request: HttpRequest, cohorte_id: int):
    cohorte = SuggestionCohorte.objects.source_cohortes().filter(id=cohorte_id).first()
    if cohorte is None:
        get_source_cohorte(cohorte_id)  # 404
    attach_counts([cohorte])
    cohorte.policy = get_policy(cohorte.type_action).describe()
    return cohorte


@router.get("/cohortes/{cohorte_id}/revue/filtres", response=FilterMetaOut)
def review_filters(request: HttpRequest, cohorte_id: int):
    cohorte = get_source_cohorte(cohorte_id)
    return {"champs": review_filter_metadata(cohorte)}


@router.get(
    "/cohortes/{cohorte_id}/groupes", response={200: GroupePageOut, 422: ErrorOut}
)
def list_groupes(request: HttpRequest, cohorte_id: int, query: Query[GroupesQuery]):
    cohorte = get_source_cohorte(cohorte_id)
    groupes = filtered_groupes(
        cohorte,
        parse_filter(query.filtre),
        parse_tuples(query.tuples),
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


@router.get(
    "/cohortes/{cohorte_id}/lignes", response={200: LignePageOut, 422: ErrorOut}
)
def list_lignes(request: HttpRequest, cohorte_id: int, query: Query[LignesQuery]):
    cohorte = cohortes.get_source_cohorte(cohorte_id)
    keys, total = revue.lignes_page(
        cohorte,
        parse_filter(query.filtre),
        revue.parse_tuples(query.tuples),
        query.afficher,
        query.page,
        query.page_size,
    )
    groupe_ids = sorted({groupe_id for groupe_id, _ in keys})
    groupes = list(groupes_queryset().filter(id__in=groupe_ids).order_by("id"))
    return {
        "items": [
            {"groupe_id": groupe_id, "key": ligne_key(groupe_id, champs)}
            for groupe_id, champs in keys
        ],
        "groupes": serialize_groupes(groupes, get_policy(cohorte.type_action)),
        "total": total,
        "page": query.page,
        "page_size": query.page_size,
    }


@router.get("/cohortes/{cohorte_id}/stats", response={200: StatsOut, 422: ErrorOut})
def review_stats(request: HttpRequest, cohorte_id: int, query: Query[StatsQuery]):
    cohorte = get_source_cohorte(cohorte_id)
    return stats(
        cohorte,
        query.vue,
        parse_filter(query.filtre),
        parse_tuples(query.tuples),
        query.afficher,
    )


@router.get("/groupes/{groupe_id}", response={200: GroupeDetailOut, 404: ErrorOut})
def groupe_detail(request: HttpRequest, groupe_id: int):
    groupe = (
        groupes_queryset()
        .filter(
            id=groupe_id,
            suggestion_cohorte__type_action__in=SOURCE_TYPE_ACTIONS,
        )
        .first()
    )
    if groupe is None:
        raise RevueApiError(404, "not_found", "Groupe introuvable")
    return serialize_groupe_detail(
        groupe, get_policy(groupe.suggestion_cohorte.type_action)
    )


@router.post("/groupes/{groupe_id}/decision", response=WRITE_RESPONSES)
def groupe_decision(request: HttpRequest, groupe_id: int, payload: GroupeDecisionIn):
    return decide_groupe(
        groupe_id, payload.action, request.auth, payload.expected_modifie_le
    )


@router.post("/groupes/{groupe_id}/lignes/decision", response=WRITE_RESPONSES)
def lignes_decision(request: HttpRequest, groupe_id: int, payload: LignesDecisionIn):
    return decide_lignes(
        groupe_id,
        payload.champs,
        payload.action,
        request.auth,
        payload.expected_modifie_le,
    )


@router.put("/groupes/{groupe_id}/propositions", response=WRITE_RESPONSES)
def upsert_proposition(request: HttpRequest, groupe_id: int, payload: PropositionIn):
    return upsert_proposition_service(
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
    return delete_proposition_service(
        groupe_id, query.suggestion_modele, query.champs, query.expected_modifie_le
    )


@router.post("/groupes/{groupe_id}/report", response=WRITE_RESPONSES)
def report(request: HttpRequest, groupe_id: int, payload: ReportIn):
    return report_service(
        groupe_id, payload.cible, payload.champs, payload.expected_modifie_le
    )


@router.get(
    "/annuaire-entreprises",
    response={200: AnnuaireEntrepriseOut, 422: ErrorOut, 502: ErrorOut},
)
def annuaire_entreprises(request: HttpRequest, query: Query[AnnuaireQuery]):
    """Entreprise and établissement of a SIRET / SIREN, from the public API
    « Recherche d'entreprises » (cached one day)."""
    return annuaire_lookup(query.champ, query.valeur)
