import pytest
from django.conf import settings
from django.test import RequestFactory

from qfdmo.views.carte import CarteConfigView, CarteSearchActeursView
from qfdmo.views.formulaire import FormulaireSearchActeursView


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
    def test_carte_search_acteurs_default(self, rf):
        request = rf.get("/fake/")
        view = CarteSearchActeursView()
        view.request = request
        assert (
            view._get_max_displayed_acteurs() == settings.CARTE_MAX_SOLUTION_DISPLAYED
        ), "On affiche 100 acteurs sur la carte standalone (ou en iframe)"

    def test_carte_search_acteurs_with_limit(self, rf):
        request = rf.get("/fake/?limit=42")
        view = CarteSearchActeursView()
        view.request = request
        assert (
            view._get_max_displayed_acteurs() == 42
        ), "On affiche le nombre d'acteurs passés en paramètre"

    def test_formulaire_search_acteurs(self, rf):
        request = rf.get("/fake/")
        view = FormulaireSearchActeursView()
        view.request = request
        assert (
            view._get_max_displayed_acteurs() == settings.DEFAULT_MAX_SOLUTION_DISPLAYED
        ), "On affiche 10 acteurs sur le formulaire (ou en iframe)"

    def test_carte_config_view(self, rf):
        request = rf.get("/fake/")
        view = CarteConfigView()
        view.request = request
        assert (
            view._get_max_displayed_acteurs() == settings.CARTE_MAX_SOLUTION_DISPLAYED
        ), "On affiche 100 acteurs sur les cartes sur mesure par défaut"
