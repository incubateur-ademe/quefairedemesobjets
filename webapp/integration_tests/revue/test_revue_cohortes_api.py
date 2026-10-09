import json

import pytest
from data.models.suggestion import (
    SuggestionAction,
    SuggestionLog,
    SuggestionStatut,
)
from django.contrib.auth.models import User
from unit_tests.data.models.suggestion_factory import (
    SuggestionCohorteFactory,
    SuggestionGroupeFactory,
)

API = "/api/suggestions"


@pytest.fixture
def client(client):
    client.force_login(User.objects.create_user(username="admin", is_superuser=True))
    return client


@pytest.fixture
def cohortes():
    ajout = SuggestionCohorteFactory(
        identifiant_action="dag_ajout",
        type_action=SuggestionAction.SOURCE_AJOUT,
        metadata={"source_code": "ecomaison"},
    )
    for statut in [SuggestionStatut.AVALIDER] * 2 + [SuggestionStatut.REJETEE]:
        SuggestionGroupeFactory(suggestion_cohorte=ajout, statut=statut)
    for niveau in ["ERROR", "WARNING", "WARNING", "INFO"]:
        SuggestionLog.objects.create(
            suggestion_cohorte=ajout,
            niveau_de_log=niveau,
            fonction_de_transformation="f",
            message=niveau,
        )
    modification = SuggestionCohorteFactory(
        identifiant_action="dag_modification",
        type_action=SuggestionAction.SOURCE_MODIFICATION,
    )
    SuggestionGroupeFactory(
        suggestion_cohorte=modification, statut=SuggestionStatut.SUCCES
    )
    # Excluded: not SOURCE, or SOURCE without groupe
    SuggestionGroupeFactory(
        suggestion_cohorte=SuggestionCohorteFactory(
            identifiant_action="dag_clustering", type_action=SuggestionAction.CLUSTERING
        )
    )
    SuggestionCohorteFactory(
        identifiant_action="dag_vide", type_action=SuggestionAction.SOURCE_AJOUT
    )
    return ajout, modification


def get(client, path, **params):
    response = client.get(f"{API}{path}", params)
    return response.status_code, response.json()


@pytest.mark.django_db
class TestListCohortes:
    def test_only_source_cohortes_with_groupes(self, client, cohortes):
        status, body = get(client, "/cohortes")

        assert status == 200
        assert body["total"] == 2
        assert {item["identifiant_action"] for item in body["items"]} == {
            "dag_ajout",
            "dag_modification",
        }

    def test_counters_and_logs(self, client, cohortes):
        _, body = get(client, "/cohortes", tri="id")

        ajout = body["items"][0]
        assert ajout["total_groupes"] == 3
        assert ajout["compteurs"]["AVALIDER"] == 2
        assert ajout["compteurs"]["REJETEE"] == 1
        assert ajout["logs"] == {"ERROR": 1, "WARNING": 2, "INFO": 1}
        assert ajout["type_action_label"].startswith("ingestion")

    def test_structured_filter_and_quick_filters(self, client, cohortes):
        filtre = {
            "op": "and",
            "conditions": [
                {
                    "field": "metadata.source_code",
                    "operator": "eq",
                    "value": "ECOMAISON",
                }
            ],
        }
        _, body = get(client, "/cohortes", filtre=json.dumps(filtre))
        assert [item["identifiant_action"] for item in body["items"]] == ["dag_ajout"]

        _, body = get(client, "/cohortes", type_action="SOURCE_MODIFICATION")
        assert [item["identifiant_action"] for item in body["items"]] == [
            "dag_modification"
        ]

    def test_sort_and_pagination(self, client, cohortes):
        _, body = get(client, "/cohortes", tri="-total_groupes", page_size=1, page=2)

        assert body["total"] == 2
        assert body["page"] == 2
        assert [item["identifiant_action"] for item in body["items"]] == [
            "dag_modification"
        ]

    @pytest.mark.parametrize(
        "params,code",
        [
            ({"filtre": "{"}, "invalid_filter"),
            ({"tri": "nom"}, "invalid_sort"),
        ],
    )
    def test_errors(self, client, cohortes, params, code):
        status, body = get(client, "/cohortes", **params)

        assert status == 422
        assert body["code"] == code

    def test_page_size_is_bounded(self, client, cohortes):
        status, _ = get(client, "/cohortes", page_size=201)
        assert status == 422


@pytest.mark.django_db
class TestFiltersMetadata:
    def test_lists_fields_and_metadata_keys(self, client, cohortes):
        status, body = get(client, "/cohortes/filtres")

        assert status == 200
        keys = [champ["key"] for champ in body["champs"]]
        assert "identifiant_action" in keys
        assert "metadata.source_code" in keys
        assert "nom" not in keys


@pytest.mark.django_db
class TestLogs:
    def test_logs_sorted_by_gravity(self, client, cohortes):
        ajout, _ = cohortes
        status, body = get(client, f"/cohortes/{ajout.id}/logs")

        assert status == 200
        assert [log["niveau"] for log in body["items"]] == [
            "ERROR",
            "WARNING",
            "WARNING",
            "INFO",
        ]

    def test_filter_by_level(self, client, cohortes):
        ajout, _ = cohortes
        _, body = get(client, f"/cohortes/{ajout.id}/logs", niveau="WARNING")
        assert body["total"] == 2

    def test_not_a_source_cohorte(self, client, cohortes):
        clustering = SuggestionCohorteFactory(type_action=SuggestionAction.CLUSTERING)
        status, _ = get(client, f"/cohortes/{clustering.id}/logs")
        assert status == 404
