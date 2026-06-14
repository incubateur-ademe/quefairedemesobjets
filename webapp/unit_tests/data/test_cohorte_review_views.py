import json

import pytest
from data.models.suggestion import SuggestionAction, SuggestionStatut
from data.models.suggestions.source import SuggestionGroupeTypeSource
from django.contrib.gis.geos import Point
from django.urls import reverse
from unit_tests.data.models.suggestion_factory import (
    SuggestionCohorteFactory,
    SuggestionGroupeFactory,
    SuggestionUnitaireFactory,
)
from unit_tests.qfdmo.acteur_factory import ActeurFactory


@pytest.fixture
def staff_user(django_user_model):
    return django_user_model.objects.create_user(
        username="staff",
        password="staff",  # pragma: allowlist secret
        is_staff=True,
    )


@pytest.fixture
def cohorte():
    return SuggestionCohorteFactory(type_action=SuggestionAction.SOURCE_AJOUT)


def _groupe_with_suggestions(cohorte, identifiant, nom, url=None, **groupe_kwargs):
    groupe = SuggestionGroupeFactory(suggestion_cohorte=cohorte, **groupe_kwargs)
    SuggestionUnitaireFactory(
        suggestion_groupe=groupe,
        suggestion_modele="Acteur",
        champs=["identifiant_unique"],
        valeurs=[identifiant],
    )
    SuggestionUnitaireFactory(
        suggestion_groupe=groupe,
        suggestion_modele="Acteur",
        champs=["nom"],
        valeurs=[nom],
    )
    if url is not None:
        SuggestionUnitaireFactory(
            suggestion_groupe=groupe,
            suggestion_modele="Acteur",
            champs=["url"],
            valeurs=[url],
        )
    return groupe


@pytest.mark.django_db
class TestCohorteReviewAccess:
    def test_anonymous_user_is_redirected(self, client, cohorte):
        for route in ["data:cohorte_review", "data:cohorte_review_rows"]:
            response = client.get(reverse(route, args=[cohorte.id]))
            assert response.status_code == 302

    def test_non_staff_user_cannot_access(self, client, django_user_model, cohorte):
        user = django_user_model.objects.create_user(username="user", password="user")
        client.force_login(user)
        for route in ["data:cohorte_review", "data:cohorte_review_rows"]:
            response = client.get(reverse(route, args=[cohorte.id]))
            assert response.status_code == 403

    def test_staff_user_can_access_review_page(self, client, staff_user, cohorte):
        client.force_login(staff_user)
        response = client.get(reverse("data:cohorte_review", args=[cohorte.id]))
        assert response.status_code == 200
        assert b"cohorte-review" in response.content


@pytest.mark.django_db
class TestCohorteReviewRows:
    def test_rows_contain_cells_and_fields_meta(self, client, staff_user, cohorte):
        groupe = _groupe_with_suggestions(
            cohorte, "ID_1", "Acteur 1", url="https://a1.fr"
        )
        client.force_login(staff_user)

        response = client.get(reverse("data:cohorte_review_rows", args=[cohorte.id]))

        assert response.status_code == 200
        payload = response.json()
        assert payload["meta"]["total"] == 1
        assert payload["meta"]["next_after"] is None

        row = payload["rows"][0]
        assert row["acteur_id"] == "ID_1"
        # the detail link targets the admin change page (the only standalone
        # detail view), not the Turbo Stream endpoint
        assert row["detail_url"] == f"/admin/data/suggestiongroupe/{groupe.id}/change/"
        assert row["statut"] == SuggestionStatut.AVALIDER
        assert row["cells"]["nom"] == {
            "current": None,
            "suggested": "Acteur 1",
            "statut": SuggestionStatut.AVALIDER,
        }
        assert row["cells"]["url"] == {
            "current": None,
            "suggested": "https://a1.fr",
            "statut": SuggestionStatut.AVALIDER,
        }

        fields = {field["key"]: field["pending"] for field in payload["meta"]["fields"]}
        assert fields == {"identifiant_unique": 1, "nom": 1, "url": 1}

    def test_cursor_pagination(self, client, staff_user, cohorte):
        groupes = [
            _groupe_with_suggestions(cohorte, f"ID_{i}", f"Acteur {i}")
            for i in range(3)
        ]
        client.force_login(staff_user)
        rows_url = reverse("data:cohorte_review_rows", args=[cohorte.id])

        first_page = client.get(rows_url, {"limit": 2}).json()
        assert [row["groupe_id"] for row in first_page["rows"]] == [
            groupes[0].id,
            groupes[1].id,
        ]
        assert first_page["meta"]["total"] == 3
        assert first_page["meta"]["next_after"] == groupes[1].id

        second_page = client.get(
            rows_url, {"limit": 2, "after": first_page["meta"]["next_after"]}
        ).json()
        assert [row["groupe_id"] for row in second_page["rows"]] == [groupes[2].id]
        assert second_page["meta"]["next_after"] is None

    def test_statut_filter_defaults_to_avalider(self, client, staff_user, cohorte):
        pending = _groupe_with_suggestions(cohorte, "ID_PENDING", "Pending")
        rejected = _groupe_with_suggestions(
            cohorte, "ID_REJECTED", "Rejected", statut=SuggestionStatut.REJETEE
        )
        client.force_login(staff_user)
        rows_url = reverse("data:cohorte_review_rows", args=[cohorte.id])

        default_page = client.get(rows_url).json()
        assert [row["groupe_id"] for row in default_page["rows"]] == [pending.id]

        all_page = client.get(rows_url, {"statut": "all"}).json()
        assert {row["groupe_id"] for row in all_page["rows"]} == {
            pending.id,
            rejected.id,
        }

    def test_champ_filter(self, client, staff_user, cohorte):
        with_url = _groupe_with_suggestions(cohorte, "ID_URL", "A", url="https://a.fr")
        _groupe_with_suggestions(cohorte, "ID_NO_URL", "B")
        client.force_login(staff_user)

        response = client.get(
            reverse("data:cohorte_review_rows", args=[cohorte.id]), {"champ": "url"}
        )

        assert [row["groupe_id"] for row in response.json()["rows"]] == [with_url.id]

    def test_q_filter_on_acteur_id(self, client, staff_user, cohorte):
        match = _groupe_with_suggestions(
            cohorte, "ID_1", "A", acteur_id="emmaus_auray_001"
        )
        _groupe_with_suggestions(cohorte, "ID_2", "B", acteur_id="ressourcerie_lorient")
        client.force_login(staff_user)

        response = client.get(
            reverse("data:cohorte_review_rows", args=[cohorte.id]), {"q": "auray"}
        )

        assert [row["groupe_id"] for row in response.json()["rows"]] == [match.id]

    def test_invalid_cursor_returns_400(self, client, staff_user, cohorte):
        client.force_login(staff_user)
        response = client.get(
            reverse("data:cohorte_review_rows", args=[cohorte.id]), {"after": "abc"}
        )
        assert response.status_code == 400

    def test_unsupported_type_action_returns_fallback_row(self, client, staff_user):
        crawl_cohorte = SuggestionCohorteFactory(
            type_action=SuggestionAction.CRAWL_URLS
        )
        groupe = SuggestionGroupeFactory(suggestion_cohorte=crawl_cohorte)
        client.force_login(staff_user)

        response = client.get(
            reverse("data:cohorte_review_rows", args=[crawl_cohorte.id])
        )

        row = response.json()["rows"][0]
        assert row["groupe_id"] == groupe.id
        assert row["cells"] == {}
        assert "error" in row


@pytest.mark.django_db
class TestCohorteReviewGroupe:
    """Single-groupe endpoint feeding the focus-mode detail drawer."""

    def test_returns_full_pivot_row(self, client, staff_user, cohorte):
        groupe = _groupe_with_suggestions(cohorte, "ID_1", "A", url="https://a.fr")
        client.force_login(staff_user)

        response = client.get(
            reverse("data:cohorte_review_groupe", args=[cohorte.id, groupe.id])
        )

        assert response.status_code == 200
        row = response.json()["row"]
        assert row["groupe_id"] == groupe.id
        # every field of the acteur is present, not just one
        assert set(row["cells"]) == {"identifiant_unique", "nom", "url"}

    def test_groupe_from_another_cohorte_is_404(self, client, staff_user, cohorte):
        other = SuggestionCohorteFactory(type_action=SuggestionAction.SOURCE_AJOUT)
        other_groupe = _groupe_with_suggestions(other, "ID_OTHER", "Other")
        client.force_login(staff_user)

        response = client.get(
            reverse("data:cohorte_review_groupe", args=[cohorte.id, other_groupe.id])
        )

        assert response.status_code == 404

    def test_requires_staff(self, client, django_user_model, cohorte):
        groupe = _groupe_with_suggestions(cohorte, "ID_1", "A")
        user = django_user_model.objects.create_user(username="u", password="u")
        client.force_login(user)

        response = client.get(
            reverse("data:cohorte_review_groupe", args=[cohorte.id, groupe.id])
        )

        assert response.status_code == 403


def _groupe_with_telephone(cohorte, telephone):
    groupe = SuggestionGroupeFactory(suggestion_cohorte=cohorte)
    SuggestionUnitaireFactory(
        suggestion_groupe=groupe,
        suggestion_modele="Acteur",
        champs=["telephone"],
        valeurs=[telephone],
    )
    return groupe


@pytest.mark.django_db
class TestCohorteReviewValueFilter:
    """Focus-mode query builder: filters on the suggested value."""

    def _get_rows(self, client, cohorte, valeur_filtre, champ="telephone"):
        return client.get(
            reverse("data:cohorte_review_rows", args=[cohorte.id]),
            {"champ": champ, "valeur_filtre": json.dumps(valeur_filtre)},
        )

    def test_startswith_filters_on_suggested_value(self, client, staff_user, cohorte):
        mobile = _groupe_with_telephone(cohorte, "07 12 34 56 78")
        _groupe_with_telephone(cohorte, "02 99 11 22 33")
        client.force_login(staff_user)

        response = self._get_rows(
            client,
            cohorte,
            {"conditions": [{"lookup": "startswith", "value": "07"}]},
        )

        payload = response.json()
        assert payload["meta"]["total"] == 1
        assert [row["groupe_id"] for row in payload["rows"]] == [mobile.id]

    def test_ou_combinator(self, client, staff_user, cohorte):
        mobile = _groupe_with_telephone(cohorte, "07 12 34 56 78")
        other_mobile = _groupe_with_telephone(cohorte, "06 99 11 22 33")
        _groupe_with_telephone(cohorte, "02 99 11 22 33")
        client.force_login(staff_user)

        response = self._get_rows(
            client,
            cohorte,
            {
                "combinator": "ou",
                "conditions": [
                    {"lookup": "startswith", "value": "07"},
                    {"lookup": "startswith", "value": "06"},
                ],
            },
        )

        assert {row["groupe_id"] for row in response.json()["rows"]} == {
            mobile.id,
            other_mobile.id,
        }

    def test_empty_lookup(self, client, staff_user, cohorte):
        empty = _groupe_with_telephone(cohorte, "")
        _groupe_with_telephone(cohorte, "02 99 11 22 33")
        client.force_login(staff_user)

        response = self._get_rows(
            client, cohorte, {"conditions": [{"lookup": "empty"}]}
        )

        assert [row["groupe_id"] for row in response.json()["rows"]] == [empty.id]

    def test_grouped_conditions(self, client, staff_user, cohorte):
        """(commence par 07 ET finit par 78) OU (commence par 02)"""
        mobile_78 = _groupe_with_telephone(cohorte, "07 12 34 56 78")
        _groupe_with_telephone(cohorte, "07 99 99 99 99")
        landline = _groupe_with_telephone(cohorte, "02 11 22 33 44")
        client.force_login(staff_user)

        response = self._get_rows(
            client,
            cohorte,
            {
                "combinator": "ou",
                "groups": [
                    {
                        "combinator": "et",
                        "conditions": [
                            {"lookup": "startswith", "value": "07"},
                            {"lookup": "endswith", "value": "78"},
                        ],
                    },
                    {
                        "combinator": "et",
                        "conditions": [{"lookup": "startswith", "value": "02"}],
                    },
                ],
            },
        )

        assert {row["groupe_id"] for row in response.json()["rows"]} == {
            mobile_78.id,
            landline.id,
        }

    def test_grouped_conditions_et_between_groups(self, client, staff_user, cohorte):
        """(commence par 07) ET (finit par 78 OU finit par 99)"""
        match = _groupe_with_telephone(cohorte, "07 12 34 56 78")
        _groupe_with_telephone(cohorte, "07 11 22 33 44")
        _groupe_with_telephone(cohorte, "02 11 22 33 78")
        client.force_login(staff_user)

        response = self._get_rows(
            client,
            cohorte,
            {
                "combinator": "et",
                "groups": [
                    {"conditions": [{"lookup": "startswith", "value": "07"}]},
                    {
                        "combinator": "ou",
                        "conditions": [
                            {"lookup": "endswith", "value": "78"},
                            {"lookup": "endswith", "value": "99"},
                        ],
                    },
                ],
            },
        )

        assert [row["groupe_id"] for row in response.json()["rows"]] == [match.id]

    @pytest.mark.parametrize(
        "valeur_filtre",
        [
            {"conditions": [{"lookup": "nope", "value": "07"}]},
            # regex is intentionally not allowed (ReDoS via Postgres)
            {"conditions": [{"lookup": "regex", "value": ".*"}]},
            {"conditions": [{"lookup": "startswith", "value": ""}]},
            {"conditions": []},
            {"combinator": "xor", "conditions": [{"lookup": "empty"}]},
            "not a dict",
            {"groups": []},
            {"groups": "not a list"},
            {"groups": [{"conditions": []}]},
            {"groups": [{"conditions": [{"lookup": "empty"}]}] * 6},
        ],
    )
    def test_invalid_payloads_return_400(
        self, client, staff_user, cohorte, valeur_filtre
    ):
        client.force_login(staff_user)
        response = self._get_rows(client, cohorte, valeur_filtre)
        assert response.status_code == 400

    def test_valeur_filtre_without_champ_returns_400(self, client, staff_user, cohorte):
        client.force_login(staff_user)
        response = client.get(
            reverse("data:cohorte_review_rows", args=[cohorte.id]),
            {
                "valeur_filtre": json.dumps(
                    {"conditions": [{"lookup": "startswith", "value": "07"}]}
                )
            },
        )
        assert response.status_code == 400

    def test_bulk_filter_scope_with_valeur_filtre(self, client, staff_user, cohorte):
        mobile = _groupe_with_telephone(cohorte, "07 12 34 56 78")
        landline = _groupe_with_telephone(cohorte, "02 99 11 22 33")
        client.force_login(staff_user)

        response = _post_bulk(
            client,
            cohorte,
            {
                "filter": {
                    "champ": "telephone",
                    "valeur_filtre": {
                        "conditions": [{"lookup": "startswith", "value": "07"}]
                    },
                },
                "champ": "telephone",
                "action": "reject",
            },
        )

        assert response.json()["applied"] == 1
        assert _unitaire_statuts(mobile)["telephone"] == SuggestionStatut.REJETEE
        assert _unitaire_statuts(landline)["telephone"] == SuggestionStatut.AVALIDER


def _post_bulk(client, cohorte, body):
    return client.post(
        reverse("data:cohorte_review_bulk", args=[cohorte.id]),
        data=body,
        content_type="application/json",
    )


def _unitaire_statuts(groupe):
    return {
        champ: unitaire.statut
        for unitaire in groupe.suggestion_unitaires.filter(suggestion_modele="Acteur")
        for champ in unitaire.champs
    }


@pytest.mark.django_db
class TestCohorteReviewBulk:
    def test_accept_one_field_keeps_groupe_pending(self, client, staff_user, cohorte):
        groupe = _groupe_with_suggestions(cohorte, "ID_1", "A", url="https://a.fr")
        client.force_login(staff_user)

        response = _post_bulk(
            client,
            cohorte,
            {"groupe_ids": [groupe.id], "champ": "url", "action": "accept"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["applied"] == 1
        assert _unitaire_statuts(groupe)["url"] == SuggestionStatut.ATRAITER
        assert _unitaire_statuts(groupe)["nom"] == SuggestionStatut.AVALIDER

        groupe.refresh_from_db()
        assert groupe.statut == SuggestionStatut.AVALIDER

        row = payload["rows"][0]
        assert row["cells"]["url"]["statut"] == SuggestionStatut.ATRAITER
        # decided fields leave the pending meta; the client keeps the column
        # and resets its counter to 0
        fields = {field["key"]: field["pending"] for field in payload["meta"]["fields"]}
        assert "url" not in fields
        assert fields["nom"] == 1

    def test_accepting_every_field_marks_groupe_atraiter(
        self, client, staff_user, cohorte
    ):
        groupe = _groupe_with_suggestions(cohorte, "ID_1", "A")
        client.force_login(staff_user)

        _post_bulk(client, cohorte, {"groupe_ids": [groupe.id], "action": "accept"})

        groupe.refresh_from_db()
        assert groupe.statut == SuggestionStatut.ATRAITER

    def test_rejecting_every_field_marks_groupe_rejetee(
        self, client, staff_user, cohorte
    ):
        groupe = _groupe_with_suggestions(cohorte, "ID_1", "A")
        client.force_login(staff_user)

        _post_bulk(client, cohorte, {"groupe_ids": [groupe.id], "action": "reject"})

        groupe.refresh_from_db()
        assert groupe.statut == SuggestionStatut.REJETEE

    def test_mixed_decisions_mark_groupe_atraiter(self, client, staff_user, cohorte):
        groupe = _groupe_with_suggestions(cohorte, "ID_1", "A")
        client.force_login(staff_user)

        _post_bulk(
            client,
            cohorte,
            {"groupe_ids": [groupe.id], "champ": "nom", "action": "reject"},
        )
        _post_bulk(
            client,
            cohorte,
            {
                "groupe_ids": [groupe.id],
                "champ": "identifiant_unique",
                "action": "accept",
            },
        )

        groupe.refresh_from_db()
        assert groupe.statut == SuggestionStatut.ATRAITER

    def test_reset_returns_groupe_to_avalider(self, client, staff_user, cohorte):
        groupe = _groupe_with_suggestions(cohorte, "ID_1", "A")
        client.force_login(staff_user)
        _post_bulk(client, cohorte, {"groupe_ids": [groupe.id], "action": "reject"})

        _post_bulk(client, cohorte, {"groupe_ids": [groupe.id], "action": "reset"})

        groupe.refresh_from_db()
        assert groupe.statut == SuggestionStatut.AVALIDER
        assert set(_unitaire_statuts(groupe).values()) == {SuggestionStatut.AVALIDER}

    def test_bulk_targets_multiple_groupes(self, client, staff_user, cohorte):
        groupes = [
            _groupe_with_suggestions(cohorte, f"ID_{i}", f"A{i}", url="https://a.fr")
            for i in range(2)
        ]
        client.force_login(staff_user)

        response = _post_bulk(
            client,
            cohorte,
            {
                "groupe_ids": [groupe.id for groupe in groupes],
                "champ": "url",
                "action": "accept",
            },
        )

        assert response.json()["applied"] == 2

    def test_groupe_from_another_cohorte_is_ignored(self, client, staff_user, cohorte):
        other_cohorte = SuggestionCohorteFactory(
            type_action=SuggestionAction.SOURCE_AJOUT
        )
        other_groupe = _groupe_with_suggestions(other_cohorte, "ID_OTHER", "Other")
        client.force_login(staff_user)

        response = _post_bulk(
            client, cohorte, {"groupe_ids": [other_groupe.id], "action": "reject"}
        )

        assert response.json()["applied"] == 0
        other_groupe.refresh_from_db()
        assert other_groupe.statut == SuggestionStatut.AVALIDER

    @pytest.mark.parametrize(
        "body",
        [
            {"groupe_ids": [1], "action": "nope"},
            {"groupe_ids": [], "action": "accept"},
            {"groupe_ids": "1,2", "action": "accept"},
            {"action": "accept"},
            {"groupe_ids": [1], "filter": {}, "action": "accept"},
            {"filter": "AVALIDER", "action": "accept"},
        ],
    )
    def test_invalid_payloads_return_400(self, client, staff_user, cohorte, body):
        client.force_login(staff_user)
        response = _post_bulk(client, cohorte, body)
        assert response.status_code == 400

    def test_filter_scope_targets_all_matching_groupes(
        self, client, staff_user, cohorte
    ):
        groupes = [
            _groupe_with_suggestions(cohorte, f"ID_{i}", f"A{i}") for i in range(3)
        ]
        already_rejected = _groupe_with_suggestions(
            cohorte, "ID_REJ", "Rej", statut=SuggestionStatut.REJETEE
        )
        client.force_login(staff_user)

        response = _post_bulk(
            client,
            cohorte,
            {"filter": {"statut": SuggestionStatut.AVALIDER}, "action": "accept"},
        )

        payload = response.json()
        # 2 unitaires (identifiant_unique + nom) per pending groupe
        assert payload["applied"] == 6
        # no rows in the response: the client reloads instead
        assert "rows" not in payload
        for groupe in groupes:
            groupe.refresh_from_db()
            assert groupe.statut == SuggestionStatut.ATRAITER
        already_rejected.refresh_from_db()
        assert already_rejected.statut == SuggestionStatut.REJETEE

    def test_filter_scope_with_champ_and_q(self, client, staff_user, cohorte):
        matching = _groupe_with_suggestions(
            cohorte, "ID_1", "A", url="https://a.fr", acteur_id="emmaus_auray"
        )
        no_url = _groupe_with_suggestions(
            cohorte, "ID_2", "B", acteur_id="emmaus_vannes"
        )
        other_q = _groupe_with_suggestions(
            cohorte, "ID_3", "C", url="https://c.fr", acteur_id="ressourcerie"
        )
        client.force_login(staff_user)

        response = _post_bulk(
            client,
            cohorte,
            {
                "filter": {"champ": "url", "q": "emmaus"},
                "champ": "url",
                "action": "reject",
            },
        )

        assert response.json()["applied"] == 1
        assert _unitaire_statuts(matching)["url"] == SuggestionStatut.REJETEE
        for untouched in [no_url, other_q]:
            assert set(_unitaire_statuts(untouched).values()) == {
                SuggestionStatut.AVALIDER
            }

    def test_filter_scope_with_exclude_ids(self, client, staff_user, cohorte):
        keep = _groupe_with_suggestions(cohorte, "ID_KEEP", "Keep")
        reject_a = _groupe_with_suggestions(cohorte, "ID_A", "A")
        reject_b = _groupe_with_suggestions(cohorte, "ID_B", "B")
        client.force_login(staff_user)

        # « rejeter tous les filtrés sauf keep »
        response = _post_bulk(
            client,
            cohorte,
            {"filter": {"exclude_ids": [keep.id]}, "action": "reject"},
        )

        assert response.status_code == 200
        keep.refresh_from_db()
        assert keep.statut == SuggestionStatut.AVALIDER
        for rejected in [reject_a, reject_b]:
            rejected.refresh_from_db()
            assert rejected.statut == SuggestionStatut.REJETEE

    def test_invalid_exclude_ids_returns_400(self, client, staff_user, cohorte):
        client.force_login(staff_user)
        response = _post_bulk(
            client,
            cohorte,
            {"filter": {"exclude_ids": ["nope"]}, "action": "reject"},
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestCohorteReviewUndo:
    def test_undo_restores_prior_per_unitaire_statut(self, client, staff_user, cohorte):
        groupe = _groupe_with_suggestions(cohorte, "ID_1", "A", url="https://a.fr")
        # nom starts accepted, url starts pending — different prior statuts
        groupe.suggestion_unitaires.filter(champs=["nom"]).update(
            statut=SuggestionStatut.ATRAITER
        )
        client.force_login(staff_user)

        # reject the whole groupe; capture the undo token
        rejected = _post_bulk(
            client, cohorte, {"groupe_ids": [groupe.id], "action": "reject"}
        ).json()
        undo_token = rejected["undo"]
        assert {entry["statut"] for entry in undo_token} == {
            SuggestionStatut.ATRAITER,
            SuggestionStatut.AVALIDER,
        }
        statuts = _unitaire_statuts(groupe)
        assert statuts["nom"] == SuggestionStatut.REJETEE
        assert statuts["url"] == SuggestionStatut.REJETEE

        # undo restores each unitaire to its individual prior statut
        # (3 changed: identifiant_unique, nom, url)
        undone = _post_bulk(
            client, cohorte, {"action": "undo", "undo": undo_token}
        ).json()
        assert undone["applied"] == 3
        statuts = _unitaire_statuts(groupe)
        assert statuts["nom"] == SuggestionStatut.ATRAITER
        assert statuts["url"] == SuggestionStatut.AVALIDER

    def test_undo_token_excludes_noop_rows(self, client, staff_user, cohorte):
        groupe = _groupe_with_suggestions(cohorte, "ID_1", "A")
        # nom already rejected: rejecting again is a no-op for it
        groupe.suggestion_unitaires.filter(champs=["nom"]).update(
            statut=SuggestionStatut.REJETEE
        )
        client.force_login(staff_user)

        rejected = _post_bulk(
            client, cohorte, {"groupe_ids": [groupe.id], "action": "reject"}
        ).json()

        # only identifiant_unique changed (nom was already rejected)
        assert rejected["applied"] == 1
        assert len(rejected["undo"]) == 1

    def test_undo_is_scoped_to_cohorte(self, client, staff_user, cohorte):
        other_cohorte = SuggestionCohorteFactory(
            type_action=SuggestionAction.SOURCE_AJOUT
        )
        other_groupe = _groupe_with_suggestions(other_cohorte, "ID_OTHER", "Other")
        other_unitaire = other_groupe.suggestion_unitaires.first()
        client.force_login(staff_user)

        # a forged token referencing another cohorte's unitaire must not apply
        response = _post_bulk(
            client,
            cohorte,
            {
                "action": "undo",
                "undo": [{"id": other_unitaire.id, "statut": SuggestionStatut.REJETEE}],
            },
        )

        assert response.json()["applied"] == 0
        other_unitaire.refresh_from_db()
        assert other_unitaire.statut == SuggestionStatut.AVALIDER

    def test_undo_rejects_pipeline_owned_statuts(self, client, staff_user, cohorte):
        """A forged undo token must not push a unitaire into a pipeline state
        (ENCOURS/ERREUR/SUCCES) the review UI never produces."""
        groupe = _groupe_with_suggestions(cohorte, "ID_1", "A")
        unitaire = groupe.suggestion_unitaires.first()
        client.force_login(staff_user)

        response = _post_bulk(
            client,
            cohorte,
            {
                "action": "undo",
                "undo": [{"id": unitaire.id, "statut": SuggestionStatut.SUCCES}],
            },
        )

        assert response.status_code == 400
        unitaire.refresh_from_db()
        assert unitaire.statut == SuggestionStatut.AVALIDER

    @pytest.mark.parametrize(
        "body",
        [
            {"action": "undo", "undo": []},
            {"action": "undo", "undo": "nope"},
            {"action": "undo", "undo": [{"id": 1, "statut": "BOGUS"}]},
            {"action": "undo", "undo": [{"id": 1, "statut": "ENCOURS"}]},
            {"action": "undo", "undo": [{"id": "x", "statut": "AVALIDER"}]},
        ],
    )
    def test_invalid_undo_returns_400(self, client, staff_user, cohorte, body):
        client.force_login(staff_user)
        assert _post_bulk(client, cohorte, body).status_code == 400


@pytest.mark.django_db
class TestSeedReviewDemoCommand:
    def test_creates_a_reviewable_cohorte(self, client, staff_user):
        from django.core.management import call_command

        for index in range(3):
            ActeurFactory(
                identifiant_unique=f"ID_SEED_{index}",
                nom=f"Acteur {index}",
                location=Point(2.1 + index / 100, 48.1),
            )

        call_command("seed_review_demo", "--groupes", "2")
        # idempotent: rerunning replaces the previous demo cohorte
        call_command("seed_review_demo", "--groupes", "2")

        cohorte = SuggestionCohorteFactory._meta.model.objects.get(
            identifiant_action="demo_revue_cohorte"
        )
        assert cohorte.suggestion_groupes.count() == 2

        client.force_login(staff_user)
        response = client.get(reverse("data:cohorte_review_rows", args=[cohorte.id]))
        payload = response.json()
        assert payload["meta"]["total"] == 2
        assert all(row["cells"] for row in payload["rows"])

    def test_fails_without_acteurs(self):
        from django.core.management import CommandError, call_command

        with pytest.raises(CommandError):
            call_command("seed_review_demo")


@pytest.mark.django_db
class TestApplySkipsRejectedUnitaires:
    def test_rejected_field_is_not_applied(self):
        cohorte = SuggestionCohorteFactory(
            type_action=SuggestionAction.SOURCE_MODIFICATION
        )
        acteur = ActeurFactory(
            identifiant_unique="ID_APPLY",
            nom="Ancien nom",
            url="https://ancien.fr",
            location=Point(2.1234, 48.1234),
        )
        groupe = SuggestionGroupeFactory(suggestion_cohorte=cohorte, acteur=acteur)
        SuggestionUnitaireFactory(
            suggestion_groupe=groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
            statut=SuggestionStatut.REJETEE,
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=groupe,
            suggestion_modele="Acteur",
            champs=["url"],
            valeurs=["https://nouveau.fr"],
            statut=SuggestionStatut.ATRAITER,
        )

        SuggestionGroupeTypeSource.from_suggestion_groupe(groupe).apply()

        acteur.refresh_from_db()
        assert acteur.nom == "Ancien nom"
        assert acteur.url == "https://nouveau.fr"
