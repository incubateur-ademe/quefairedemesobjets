import pytest
from data.models.suggestion import (
    SuggestionAction,
    SuggestionGroupe,
    SuggestionStatut,
    SuggestionUnitaire,
)
from django.urls import reverse
from unit_tests.data.models.suggestion_factory import (
    SuggestionCohorteFactory,
    SuggestionGroupeFactory,
    SuggestionUnitaireFactory,
)
from unit_tests.qfdmo.acteur_factory import ActeurFactory, RevisionActeurFactory


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


def _groupe_with_suggestions(cohorte, identifiant, nom, **groupe_kwargs):
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
    return groupe


def _post_bulk(client, cohorte, body):
    return client.post(
        reverse("data:cohorte_review_acteurs_bulk", args=[cohorte.id]),
        data=body,
        content_type="application/json",
    )


@pytest.mark.django_db
class TestCohorteReviewActeursAccess:
    def test_anonymous_user_is_redirected(self, client, cohorte):
        response = client.get(reverse("data:cohorte_review_acteurs", args=[cohorte.id]))
        assert response.status_code == 302

    def test_non_staff_user_cannot_access(self, client, django_user_model, cohorte):
        user = django_user_model.objects.create_user(username="u", password="u")
        client.force_login(user)
        routes = ["data:cohorte_review_acteurs", "data:cohorte_review_acteurs_bulk"]
        for route in routes:
            response = client.get(reverse(route, args=[cohorte.id]))
            assert response.status_code == 403

    def test_staff_user_can_access(self, client, staff_user, cohorte):
        _groupe_with_suggestions(cohorte, "ID_1", "Acteur 1")
        client.force_login(staff_user)
        response = client.get(reverse("data:cohorte_review_acteurs", args=[cohorte.id]))
        assert response.status_code == 200
        assert b"data-cohorte-review-acteurs" in response.content


@pytest.mark.django_db
class TestCohorteReviewActeursList:
    def test_renders_one_card_per_groupe_with_anchors(
        self, client, staff_user, cohorte
    ):
        groupe = _groupe_with_suggestions(cohorte, "ID_1", "Acteur 1")
        client.force_login(staff_user)

        response = client.get(reverse("data:cohorte_review_acteurs", args=[cohorte.id]))

        content = response.content.decode()
        assert f'data-groupe-id="{groupe.id}"' in content
        assert "data-card-checkbox-slot" in content
        assert "data-card-map-slot" in content
        assert f'data-groupe-statut="{SuggestionStatut.AVALIDER}"' in content

    def test_pagination_caps_at_100_per_page(self, client, staff_user, cohorte):
        for i in range(101):
            _groupe_with_suggestions(cohorte, f"ID_{i}", f"A{i}")
        client.force_login(staff_user)
        url = reverse("data:cohorte_review_acteurs", args=[cohorte.id])

        first = client.get(url)
        assert first.context["page_obj"].number == 1
        assert len(first.context["cards"]) == 100
        assert first.context["paginator"].num_pages == 2
        assert first.context["total"] == 101
        assert first.context["page_obj"].has_next() is True

        second = client.get(url, {"page": 2})
        assert len(second.context["cards"]) == 1
        assert second.context["page_obj"].has_previous() is True

    def test_out_of_range_page_is_clamped(self, client, staff_user, cohorte):
        _groupe_with_suggestions(cohorte, "ID_1", "A")
        client.force_login(staff_user)
        url = reverse("data:cohorte_review_acteurs", args=[cohorte.id])

        response = client.get(url, {"page": 999})
        assert response.context["page_obj"].number == 1

    def test_statut_filter(self, client, staff_user, cohorte):
        pending = _groupe_with_suggestions(cohorte, "ID_P", "Pending")
        rejected = _groupe_with_suggestions(
            cohorte, "ID_R", "Rejected", statut=SuggestionStatut.REJETEE
        )
        client.force_login(staff_user)
        url = reverse("data:cohorte_review_acteurs", args=[cohorte.id])

        all_page = client.get(url)
        assert {card["groupe"].id for card in all_page.context["cards"]} == {
            pending.id,
            rejected.id,
        }

        avalider = client.get(url, {"statut": SuggestionStatut.AVALIDER})
        assert [card["groupe"].id for card in avalider.context["cards"]] == [pending.id]

    def test_invalid_statut_returns_400(self, client, staff_user, cohorte):
        client.force_login(staff_user)
        response = client.get(
            reverse("data:cohorte_review_acteurs", args=[cohorte.id]),
            {"statut": "BOGUS"},
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestCohorteReviewActeursDjangoQL:
    def test_valid_djangoql_filters(self, client, staff_user, cohorte):
        with_parent = _groupe_with_suggestions(
            cohorte, "ID_P", "A", parent_revision_acteur=RevisionActeurFactory()
        )
        _groupe_with_suggestions(cohorte, "ID_N", "B")
        client.force_login(staff_user)

        response = client.get(
            reverse("data:cohorte_review_acteurs", args=[cohorte.id]),
            {"djangoql": "has_parent = True"},
        )

        assert response.status_code == 200
        assert [card["groupe"].id for card in response.context["cards"]] == [
            with_parent.id
        ]

    def test_djangoql_on_suggestion_unitaires_count(self, client, staff_user, cohorte):
        _groupe_with_suggestions(cohorte, "ID_2SU", "A")  # 2 unitaires
        single = SuggestionGroupeFactory(suggestion_cohorte=cohorte)
        SuggestionUnitaireFactory(
            suggestion_groupe=single,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Solo"],
        )
        client.force_login(staff_user)

        response = client.get(
            reverse("data:cohorte_review_acteurs", args=[cohorte.id]),
            {"djangoql": "suggestion_unitaires_count = 1"},
        )

        assert [card["groupe"].id for card in response.context["cards"]] == [single.id]

    @pytest.mark.parametrize(
        "djangoql",
        [
            "this is not valid (((",
            "unknown_field = 1",
            "has_parent = ",
        ],
    )
    def test_invalid_djangoql_returns_400(self, client, staff_user, cohorte, djangoql):
        client.force_login(staff_user)
        response = client.get(
            reverse("data:cohorte_review_acteurs", args=[cohorte.id]),
            {"djangoql": djangoql},
        )
        assert response.status_code == 400

    def test_400_message_is_controlled_not_a_stack_trace(
        self, client, staff_user, cohorte
    ):
        client.force_login(staff_user)
        response = client.get(
            reverse("data:cohorte_review_acteurs", args=[cohorte.id]),
            {"djangoql": "this is not valid ((("},
        )
        assert response.status_code == 400
        body = response.content.decode()
        assert body == "requête DjangoQL invalide"
        assert "Traceback" not in body


@pytest.mark.django_db
class TestCohorteReviewActeursBulk:
    def test_accept_sets_groupe_atraiter(self, client, staff_user, cohorte):
        groupe = _groupe_with_suggestions(cohorte, "ID_1", "A")
        client.force_login(staff_user)

        response = _post_bulk(
            client, cohorte, {"groupe_ids": [groupe.id], "action": "accept"}
        )

        assert response.status_code == 200
        assert response.json()["applied"] == 1
        groupe.refresh_from_db()
        assert groupe.statut == SuggestionStatut.ATRAITER

    def test_reject_sets_groupe_rejetee(self, client, staff_user, cohorte):
        groupe = _groupe_with_suggestions(cohorte, "ID_1", "A")
        client.force_login(staff_user)

        _post_bulk(client, cohorte, {"groupe_ids": [groupe.id], "action": "reject"})

        groupe.refresh_from_db()
        assert groupe.statut == SuggestionStatut.REJETEE

    def test_apply_to_correction_creates_revision_suggestions(
        self, client, staff_user, cohorte
    ):
        acteur = ActeurFactory()
        groupe = SuggestionGroupeFactory(suggestion_cohorte=cohorte, acteur=acteur)
        SuggestionUnitaireFactory(
            suggestion_groupe=groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )
        client.force_login(staff_user)

        response = _post_bulk(
            client,
            cohorte,
            {"groupe_ids": [groupe.id], "action": "apply_to_correction"},
        )

        assert response.json()["applied"] == 1
        revision = groupe.suggestion_unitaires.get(suggestion_modele="RevisionActeur")
        assert revision.valeurs == ["Nouveau nom"]
        assert revision.revision_acteur_id == acteur.pk

    def test_apply_to_parent_creates_parent_suggestions(
        self, client, staff_user, cohorte
    ):
        acteur = ActeurFactory()
        parent = RevisionActeurFactory()
        groupe = SuggestionGroupeFactory(
            suggestion_cohorte=cohorte, acteur=acteur, parent_revision_acteur=parent
        )
        SuggestionUnitaireFactory(
            suggestion_groupe=groupe,
            suggestion_modele="Acteur",
            champs=["nom"],
            valeurs=["Nouveau nom"],
        )
        client.force_login(staff_user)

        response = _post_bulk(
            client, cohorte, {"groupe_ids": [groupe.id], "action": "apply_to_parent"}
        )

        assert response.json()["applied"] == 1
        parent_su = groupe.suggestion_unitaires.get(
            suggestion_modele="ParentRevisionActeur"
        )
        assert parent_su.valeurs == ["Nouveau nom"]
        assert parent_su.parent_revision_acteur_id == parent.pk

    def test_apply_to_parent_skips_groupe_without_parent(
        self, client, staff_user, cohorte
    ):
        groupe = _groupe_with_suggestions(cohorte, "ID_1", "A")
        client.force_login(staff_user)

        response = _post_bulk(
            client, cohorte, {"groupe_ids": [groupe.id], "action": "apply_to_parent"}
        )

        assert response.json()["applied"] == 0
        assert not groupe.suggestion_unitaires.filter(
            suggestion_modele="ParentRevisionActeur"
        ).exists()

    def test_filter_scope_targets_all_matching_groupes(
        self, client, staff_user, cohorte
    ):
        pending = [
            _groupe_with_suggestions(cohorte, f"ID_{i}", f"A{i}") for i in range(3)
        ]
        rejected = _groupe_with_suggestions(
            cohorte, "ID_R", "R", statut=SuggestionStatut.REJETEE
        )
        client.force_login(staff_user)

        response = _post_bulk(
            client,
            cohorte,
            {"filter": {"statut": SuggestionStatut.AVALIDER}, "action": "accept"},
        )

        assert response.json()["applied"] == 3
        for groupe in pending:
            groupe.refresh_from_db()
            assert groupe.statut == SuggestionStatut.ATRAITER
        rejected.refresh_from_db()
        assert rejected.statut == SuggestionStatut.REJETEE

    def test_filter_scope_with_djangoql(self, client, staff_user, cohorte):
        with_parent = _groupe_with_suggestions(
            cohorte, "ID_P", "A", parent_revision_acteur=RevisionActeurFactory()
        )
        without_parent = _groupe_with_suggestions(cohorte, "ID_N", "B")
        client.force_login(staff_user)

        response = _post_bulk(
            client,
            cohorte,
            {"filter": {"djangoql": "has_parent = True"}, "action": "reject"},
        )

        assert response.json()["applied"] == 1
        with_parent.refresh_from_db()
        without_parent.refresh_from_db()
        assert with_parent.statut == SuggestionStatut.REJETEE
        assert without_parent.statut == SuggestionStatut.AVALIDER

    def test_groupe_from_another_cohorte_is_ignored(self, client, staff_user, cohorte):
        other = SuggestionCohorteFactory(type_action=SuggestionAction.SOURCE_AJOUT)
        other_groupe = _groupe_with_suggestions(other, "ID_OTHER", "Other")
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
            {"filter": {"djangoql": "bad ((("}, "action": "accept"},
            {"filter": {"statut": "BOGUS"}, "action": "accept"},
        ],
    )
    def test_invalid_payloads_return_400(self, client, staff_user, cohorte, body):
        client.force_login(staff_user)
        response = _post_bulk(client, cohorte, body)
        assert response.status_code == 400

    def test_unparsable_json_returns_400(self, client, staff_user, cohorte):
        client.force_login(staff_user)
        response = client.post(
            reverse("data:cohorte_review_acteurs_bulk", args=[cohorte.id]),
            data="not json",
            content_type="application/json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestCohorteReviewActeursScopingHelpers:
    """Guards the « total filtered » contract: the list and the bulk filter
    scope must always agree on what « filtered » means."""

    def test_list_total_matches_bulk_filter_applied(self, client, staff_user, cohorte):
        for i in range(4):
            _groupe_with_suggestions(cohorte, f"ID_{i}", f"A{i}")
        _groupe_with_suggestions(cohorte, "ID_R", "R", statut=SuggestionStatut.REJETEE)
        client.force_login(staff_user)

        listed = client.get(
            reverse("data:cohorte_review_acteurs", args=[cohorte.id]),
            {"statut": SuggestionStatut.AVALIDER},
        )
        assert listed.context["total"] == 4

        applied = _post_bulk(
            client,
            cohorte,
            {"filter": {"statut": SuggestionStatut.AVALIDER}, "action": "accept"},
        ).json()["applied"]
        assert applied == 4

    def test_bulk_does_not_leak_other_cohorte_via_filter(
        self, client, staff_user, cohorte
    ):
        _groupe_with_suggestions(cohorte, "ID_1", "A")
        other = SuggestionCohorteFactory(type_action=SuggestionAction.SOURCE_AJOUT)
        other_groupe = _groupe_with_suggestions(other, "ID_OTHER", "Other")
        client.force_login(staff_user)

        _post_bulk(client, cohorte, {"filter": {}, "action": "reject"})

        other_groupe.refresh_from_db()
        assert other_groupe.statut == SuggestionStatut.AVALIDER
        # sanity: the cohorte's own groupe was rejected
        assert (
            SuggestionGroupe.objects.filter(
                suggestion_cohorte=cohorte, statut=SuggestionStatut.REJETEE
            ).count()
            == 1
        )

    def test_apply_does_not_touch_suggestion_unitaire_statuts(
        self, client, staff_user, cohorte
    ):
        """Distinct from the per-field bulk endpoint: accept/reject here is a
        groupe-level statut change and must not mutate unitaire statuts."""
        groupe = _groupe_with_suggestions(cohorte, "ID_1", "A")
        client.force_login(staff_user)

        _post_bulk(client, cohorte, {"groupe_ids": [groupe.id], "action": "reject"})

        unitaire_statuts = set(
            SuggestionUnitaire.objects.filter(suggestion_groupe=groupe).values_list(
                "statut", flat=True
            )
        )
        assert unitaire_statuts == {SuggestionStatut.AVALIDER}
