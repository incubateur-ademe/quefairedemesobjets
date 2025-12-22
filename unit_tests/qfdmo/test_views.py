import pytest
from django.test import RequestFactory, override_settings

from qfdmo.views.carte import CarteConfigView, CarteSearchActeursView
from qfdmo.views.formulaire import FormulaireSearchActeursView
from unit_tests.qfdmo.carte_config_factory import CarteConfigFactory


class TestConfigurateur:
    def test_anonymous_user_cannot_access_configurateur(self, client):
        response = client.get("/iframe/configurateur")
        assert response.status_code == 302
        assert response.url.startswith("/admin")

    def test_authenticated_user_can_access_configurateur(
        self, client, django_user_model
    ):
        user = django_user_model.objects.create_user(
            username="Jean-Michel", password="accedeauconfigurateur"
        )
        client.force_login(user)
        response = client.get("/iframe/configurateur")
        assert response.status_code == 200


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
class TestCarteViews:
    @override_settings(CARTE_MAX_SOLUTION_DISPLAYED=123)
    def test_carte_search_acteurs_default(self, rf):
        request = rf.get("/fake/")
        view = CarteSearchActeursView()
        view.request = request
        assert (
            view._get_max_displayed_acteurs() == 123
        ), "On affiche 100 acteurs sur la carte standalone (ou en iframe)"

    @override_settings(CARTE_MAX_SOLUTION_DISPLAYED=123)
    def test_carte_search_acteurs_with_limit(self, rf):
        request = rf.get("/fake/?limit=42")
        view = CarteSearchActeursView()
        view.request = request
        assert (
            view._get_max_displayed_acteurs() == 42
        ), "On affiche le nombre d'acteurs passés en paramètre"

    @override_settings(DEFAULT_MAX_SOLUTION_DISPLAYED=456)
    def test_formulaire_search_acteurs(self, rf):
        request = rf.get("/fake/")
        view = FormulaireSearchActeursView()
        view.request = request
        assert (
            view._get_max_displayed_acteurs() == 456
        ), "On affiche 10 acteurs sur le formulaire (ou en iframe)"

    @override_settings(CARTE_MAX_SOLUTION_DISPLAYED=25)
    def test_carte_config_view(self, rf):
        carte_config = CarteConfigFactory()
        request = rf.get("/fake/")
        view = CarteConfigView()
        view.request = request
        view.kwargs = {"slug": carte_config.slug}
        assert (
            view._get_max_displayed_acteurs() == 25
        ), "On affiche 25 acteurs sur les cartes sur mesure par défaut"

    def test_cache_key_same_for_different_view_modes(self, rf):
        """Test that cache key is the same when only view mode changes."""
        # First request in carte mode
        request1 = rf.get(
            "/carte?latitude=48.8566&longitude=2.3522&action_list=reparer"
        )
        view1 = CarteSearchActeursView()
        view1.request = request1
        cache_key1 = view1._get_cache_key_for_acteurs()

        # Second request in liste mode (same params except view mode)
        request2 = rf.get(
            "/carte?latitude=48.8566&longitude=2.3522&action_list=reparer&view_mode-view=liste"
        )
        view2 = CarteSearchActeursView()
        view2.request = request2
        cache_key2 = view2._get_cache_key_for_acteurs()

        # Cache keys should be the same
        assert cache_key1 == cache_key2

    def test_cache_key_different_for_different_params(self, rf):
        """Test that cache key differs when search parameters change."""
        # Request with reparer action
        request1 = rf.get(
            "/carte?latitude=48.8566&longitude=2.3522&action_list=reparer"
        )
        view1 = CarteSearchActeursView()
        view1.request = request1
        cache_key1 = view1._get_cache_key_for_acteurs()

        # Request with donner action
        request2 = rf.get("/carte?latitude=48.8566&longitude=2.3522&action_list=donner")
        view2 = CarteSearchActeursView()
        view2.request = request2
        cache_key2 = view2._get_cache_key_for_acteurs()

        # Cache keys should be different
        assert cache_key1 != cache_key2

    def test_cache_key_ignores_page_number(self, rf):
        """Test that cache key is the same regardless of page number."""
        # Request without page
        request1 = rf.get(
            "/carte?latitude=48.8566&longitude=2.3522&action_list=reparer"
        )
        view1 = CarteSearchActeursView()
        view1.request = request1
        cache_key1 = view1._get_cache_key_for_acteurs()

        # Request with page=2
        request2 = rf.get(
            "/carte?latitude=48.8566&longitude=2.3522&action_list=reparer&page=2"
        )
        view2 = CarteSearchActeursView()
        view2.request = request2
        cache_key2 = view2._get_cache_key_for_acteurs()

        # Cache keys should be the same
        assert cache_key1 == cache_key2
