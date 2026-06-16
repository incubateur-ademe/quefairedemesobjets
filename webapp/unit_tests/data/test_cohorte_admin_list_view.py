import pytest
from data.models.suggestion import (
    SuggestionAction,
    SuggestionCohorteStatut,
    SuggestionStatut,
)
from django.urls import reverse
from unit_tests.data.models.suggestion_factory import (
    SuggestionCohorteFactory,
    SuggestionGroupeFactory,
)


@pytest.fixture
def superuser(django_user_model):
    return django_user_model.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="pwd",  # pragma: allowlist secret
    )


@pytest.fixture
def staff_user(django_user_model):
    return django_user_model.objects.create_user(
        username="staffer",
        email="staff@example.com",
        password="pwd",  # pragma: allowlist secret
        is_staff=True,
    )


@pytest.fixture
def client_logged(client, superuser):
    client.force_login(superuser)
    return client


def _cohorte_with_groupes(pending=0, decided=0, **kwargs):
    cohorte = SuggestionCohorteFactory(**kwargs)
    for _ in range(pending):
        SuggestionGroupeFactory(
            suggestion_cohorte=cohorte, statut=SuggestionStatut.AVALIDER
        )
    for _ in range(decided):
        SuggestionGroupeFactory(
            suggestion_cohorte=cohorte, statut=SuggestionStatut.ATRAITER
        )
    return cohorte


def _ids(response):
    return [c.id for c in response.context["cohortes"]]


@pytest.mark.django_db
class TestCohortAdminListView:
    def url(self, **params):
        base = reverse("data:cohorte_admin_list")
        if params:
            from urllib.parse import urlencode

            return f"{base}?{urlencode(params)}"
        return base

    # ------------------------------------------------------------------ #
    # AC-20.1 — Accès (IsSuperuserMixin)
    # ------------------------------------------------------------------ #

    def test_ac_20_1_1_superuser_gets_200_with_context(self, client_logged):
        _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url())
        assert response.status_code == 200
        for key in ("cohortes", "page_obj", "paginator", "columns", "filters"):
            assert key in response.context

    def test_ac_20_1_2_non_superuser_staff_is_forbidden(self, client, staff_user):
        client.force_login(staff_user)
        response = client.get(self.url())
        assert response.status_code == 403

    def test_ac_20_1_3_anonymous_is_redirected_to_login(self, client):
        response = client.get(self.url())
        assert response.status_code == 302

    # ------------------------------------------------------------------ #
    # AC-20.2 — Exclusion des cohortes sans groupe
    # ------------------------------------------------------------------ #

    def test_ac_20_2_1_excludes_cohortes_without_groupes(self, client_logged):
        SuggestionCohorteFactory()  # no groupes
        kept = _cohorte_with_groupes(pending=1)

        response = client_logged.get(self.url())

        assert _ids(response) == [kept.id]
        assert response.context["paginator"].count == 1

    def test_ac_20_2_2_zero_groupe_never_appears_even_with_filter(self, client_logged):
        SuggestionCohorteFactory(identifiant_action="match_me")  # no groupes
        response = client_logged.get(self.url(identifiant_action="match_me"))
        assert _ids(response) == []
        assert response.context["paginator"].count == 0

    # ------------------------------------------------------------------ #
    # AC-20.3 — Pagination
    # ------------------------------------------------------------------ #

    def test_ac_20_3_1_high_page_clamped_to_last(self, client_logged):
        for _ in range(3):
            _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url(page=999))
        assert response.context["page_obj"].number == 1

    def test_ac_20_3_2_non_integer_page_falls_back_to_one(self, client_logged):
        _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url(page="abc"))
        assert response.status_code == 200
        assert response.context["page_obj"].number == 1

    @pytest.mark.parametrize("page", ["0", "-5"])
    def test_ac_20_3_3_non_positive_page_falls_back_to_one(self, client_logged, page):
        _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url(page=page))
        assert response.context["page_obj"].number == 1

    def test_ac_20_3_4_page_size_is_100(self, client_logged):
        for _ in range(150):
            _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url())
        assert len(response.context["cohortes"]) == 100
        assert response.context["paginator"].num_pages == 2
        assert response.context["paginator"].count == 150

    def test_ac_20_3_5_empty_result_message_and_pagination(self, client_logged):
        _cohorte_with_groupes(pending=1, identifiant_action="alpha")
        response = client_logged.get(self.url(identifiant_action="zzz_no_match"))
        assert response.context["paginator"].count == 0
        content = response.content.decode()
        assert "Aucune cohorte ne correspond à ces critères." in content
        assert "Page 1 sur 1 · 0 cohortes" in content

    def test_ac_20_3_6_pagination_text_format(self, client_logged):
        for _ in range(150):
            _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url())
        assert "Page 1 sur 2 · 150 cohortes" in response.content.decode()

    # ------------------------------------------------------------------ #
    # AC-20.4 — Tri
    # ------------------------------------------------------------------ #

    def test_ac_20_4_1_default_sort_is_date_desc(self, client_logged):
        older = _cohorte_with_groupes(pending=1)
        newer = _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url())
        assert _ids(response) == [newer.id, older.id]
        assert response.context["sort"]["field"] == "date"
        assert response.context["sort"]["dir"] == "desc"

    def test_ac_20_4_2_sort_by_id_asc(self, client_logged):
        a = _cohorte_with_groupes(pending=1)
        b = _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url(sort="id", dir="asc"))
        assert _ids(response) == sorted([a.id, b.id])

    def test_ac_20_4_3_sort_by_id_desc(self, client_logged):
        a = _cohorte_with_groupes(pending=1)
        b = _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url(sort="id", dir="desc"))
        assert _ids(response) == sorted([a.id, b.id], reverse=True)

    def test_ac_20_4_4_sort_progression_on_pending_desc(self, client_logged):
        few = _cohorte_with_groupes(pending=2)
        many = _cohorte_with_groupes(pending=5)
        response = client_logged.get(self.url(sort="progression", dir="desc"))
        assert _ids(response) == [many.id, few.id]

    def test_ac_20_4_5_unknown_sort_falls_back_to_default(self, client_logged):
        _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url(sort="bogus"))
        assert response.context["sort"]["field"] == "date"
        assert response.context["sort"]["dir"] == "desc"

    def test_ac_20_4_6_invalid_dir_on_non_default_column_is_asc(self, client_logged):
        _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url(sort="id", dir="weird"))
        assert response.context["sort"]["field"] == "id"
        assert response.context["sort"]["dir"] == "asc"

    def test_ac_20_4_7_invalid_dir_on_default_column_is_desc(self, client_logged):
        _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url(sort="date", dir="weird"))
        assert response.context["sort"]["field"] == "date"
        assert response.context["sort"]["dir"] == "desc"

    @pytest.mark.parametrize(
        "sort_key",
        ["id", "action", "execution", "statut", "progression", "date"],
    )
    def test_ac_20_4_8_all_columns_are_sortable(self, client_logged, sort_key):
        _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url(sort=sort_key, dir="asc"))
        assert response.context["sort"]["field"] == sort_key

    # ------------------------------------------------------------------ #
    # AC-20.5 — Conservation du tri / réinitialisation de la page
    # ------------------------------------------------------------------ #

    def test_ac_20_5_1_pagination_links_keep_sort(self, client_logged):
        for _ in range(150):
            _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url(sort="id", dir="asc"))
        content = response.content.decode()
        # the "Suivant" link must carry sort + dir
        assert "sort=id" in content
        assert "dir=asc" in content

    def test_ac_20_5_2_sort_headers_reset_page_to_one(self, client_logged):
        for _ in range(150):
            _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url(page=2, sort="id", dir="asc"))
        content = response.content.decode()
        # every column header sort link forces page=1
        assert "page=1" in content
        assert content.count('class="th-sort') == 6

    def test_ac_20_5_3_pagination_links_keep_filters(self, client_logged):
        for _ in range(150):
            _cohorte_with_groupes(pending=1, identifiant_action="keepme")
        response = client_logged.get(self.url(identifiant_action="keepme"))
        content = response.content.decode()
        assert "identifiant_action=keepme" in content

    def test_ac_20_5_4_filter_form_carries_sort_hidden_fields(self, client_logged):
        _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url(sort="id", dir="asc"))
        content = response.content.decode()
        assert '<input type="hidden" name="sort" value="id" />' in content
        assert '<input type="hidden" name="dir" value="asc" />' in content

    # ------------------------------------------------------------------ #
    # AC-20.6 — Filtres « champs de la cohorte »
    # ------------------------------------------------------------------ #

    def test_ac_20_6_1_filter_identifiant_action_partial_ci(self, client_logged):
        match = _cohorte_with_groupes(pending=1, identifiant_action="ma_source_dag")
        _cohorte_with_groupes(pending=1, identifiant_action="autre")
        response = client_logged.get(self.url(identifiant_action="SOURCE"))
        assert _ids(response) == [match.id]

    def test_ac_20_6_2_filter_statut_exact(self, client_logged):
        avalider = _cohorte_with_groupes(
            pending=1, statut=SuggestionCohorteStatut.AVALIDER
        )
        _cohorte_with_groupes(pending=1, statut=SuggestionCohorteStatut.SUCCES)
        response = client_logged.get(self.url(statut=SuggestionCohorteStatut.AVALIDER))
        assert _ids(response) == [avalider.id]

    def test_ac_20_6_3_invalid_statut_ignored(self, client_logged):
        _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url(statut="NOPE"))
        assert response.context["paginator"].count == 1
        assert response.context["filters"]["statut"] == ""

    def test_ac_20_6_4_filter_type_action(self, client_logged):
        match = _cohorte_with_groupes(
            pending=1, type_action=SuggestionAction.CLUSTERING
        )
        _cohorte_with_groupes(pending=1, type_action=SuggestionAction.CRAWL_URLS)
        response = client_logged.get(self.url(type_action=SuggestionAction.CLUSTERING))
        assert _ids(response) == [match.id]

    def test_ac_20_6_5_invalid_type_action_ignored(self, client_logged):
        _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url(type_action="NOPE"))
        assert response.context["paginator"].count == 1
        assert response.context["filters"]["type_action"] == ""

    # ------------------------------------------------------------------ #
    # AC-20.7 — Filtre numérique « groupes restant à valider »
    # ------------------------------------------------------------------ #

    @pytest.mark.parametrize(
        "op,val,expected_pendings",
        [
            ("eq", "2", {2}),
            ("ne", "2", {0, 5}),
            ("lt", "2", {0}),
            ("lte", "2", {0, 2}),
            ("gt", "2", {5}),
            ("gte", "2", {2, 5}),
        ],
    )
    def test_ac_20_7_1_to_6_numeric_operators(
        self, client_logged, op, val, expected_pendings
    ):
        by_pending = {
            0: _cohorte_with_groupes(pending=0, decided=1),
            2: _cohorte_with_groupes(pending=2),
            5: _cohorte_with_groupes(pending=5),
        }
        response = client_logged.get(self.url(reste_op=op, reste_val=val))
        expected_ids = {by_pending[p].id for p in expected_pendings}
        assert set(_ids(response)) == expected_ids

    def test_ac_20_7_7_op_without_value_ignored(self, client_logged):
        _cohorte_with_groupes(pending=2)
        response = client_logged.get(self.url(reste_op="gt"))
        assert response.context["paginator"].count == 1

    def test_ac_20_7_8_value_without_op_ignored(self, client_logged):
        _cohorte_with_groupes(pending=2)
        response = client_logged.get(self.url(reste_val="2"))
        assert response.context["paginator"].count == 1

    @pytest.mark.parametrize("val", ["3.5", "abc"])
    def test_ac_20_7_9_non_integer_value_ignored(self, client_logged, val):
        _cohorte_with_groupes(pending=2)
        response = client_logged.get(self.url(reste_op="gt", reste_val=val))
        assert response.context["paginator"].count == 1

    def test_ac_20_7_9_non_integer_value_keeps_other_filters(self, client_logged):
        match = _cohorte_with_groupes(pending=2, identifiant_action="keepme")
        _cohorte_with_groupes(pending=2, identifiant_action="other")
        response = client_logged.get(
            self.url(reste_op="gt", reste_val="abc", identifiant_action="keepme")
        )
        assert _ids(response) == [match.id]

    def test_ac_20_7_10_negative_value_ignored(self, client_logged):
        _cohorte_with_groupes(pending=2)
        response = client_logged.get(self.url(reste_op="gt", reste_val="-1"))
        assert response.context["paginator"].count == 1

    # ------------------------------------------------------------------ #
    # AC-20.8 — Combinaison de filtres (ET implicite)
    # ------------------------------------------------------------------ #

    def test_ac_20_8_1_type_action_and_identifiant_combined(self, client_logged):
        match = _cohorte_with_groupes(
            pending=1,
            type_action=SuggestionAction.CLUSTERING,
            identifiant_action="ma_source_dag",
        )
        # right type, wrong identifiant
        _cohorte_with_groupes(
            pending=1,
            type_action=SuggestionAction.CLUSTERING,
            identifiant_action="autre",
        )
        # right identifiant, wrong type
        _cohorte_with_groupes(
            pending=1,
            type_action=SuggestionAction.CRAWL_URLS,
            identifiant_action="ma_source_dag",
        )
        response = client_logged.get(
            self.url(
                type_action=SuggestionAction.CLUSTERING, identifiant_action="SOURCE"
            )
        )
        assert _ids(response) == [match.id]

    def test_ac_20_8_2_statut_numeric_and_identifiant_combined(self, client_logged):
        match = _cohorte_with_groupes(
            pending=5,
            statut=SuggestionCohorteStatut.AVALIDER,
            identifiant_action="dag_target",
        )
        # right statut + identifiant, too few pending
        _cohorte_with_groupes(
            pending=1,
            statut=SuggestionCohorteStatut.AVALIDER,
            identifiant_action="dag_target",
        )
        # enough pending + identifiant, wrong statut
        _cohorte_with_groupes(
            pending=5,
            statut=SuggestionCohorteStatut.SUCCES,
            identifiant_action="dag_target",
        )
        # right statut + pending, no identifiant match
        _cohorte_with_groupes(
            pending=5,
            statut=SuggestionCohorteStatut.AVALIDER,
            identifiant_action="other",
        )
        response = client_logged.get(
            self.url(
                statut=SuggestionCohorteStatut.AVALIDER,
                reste_op="gt",
                reste_val="2",
                identifiant_action="target",
            )
        )
        assert _ids(response) == [match.id]

    # ------------------------------------------------------------------ #
    # AC-20.9 — Réinitialiser
    # ------------------------------------------------------------------ #

    def test_ac_20_9_1_bare_url_is_default_state(self, client_logged):
        _cohorte_with_groupes(pending=1)
        response = client_logged.get(self.url())
        filters = response.context["filters"]
        assert all(value == "" for value in filters.values())
        assert response.context["sort"]["field"] == "date"
        assert response.context["sort"]["dir"] == "desc"
