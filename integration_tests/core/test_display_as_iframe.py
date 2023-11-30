import pytest
from django.core.management import call_command

from qfdmo.models.action import CachedDirectionAction


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            "action_directions",
            "actions",
        )
        CachedDirectionAction.reload_cache()


class TestDisplayAsIframe:
    @pytest.mark.django_db
    def test_display_as_iframe(self, client):
        url = "?iframe"

        response = client.get(url)

        assert response.status_code == 200
        assert 'class="fr-header' not in str(response.content)
        assert 'class="fr-footer' not in str(response.content)
        assert (
            "Retrouvez les bonnes adresses sur <a "
            'href="https://longuevieauxobjets.ademe.fr/" target="_blank" rel="noopener"'
            ">longuevieauxobjets.ademe.fr</a>" in str(response.content)
        )

    @pytest.mark.django_db
    def test_display_as_no_iframe(self, client):
        url = ""

        response = client.get(url)

        assert response.status_code == 200
        assert 'class="fr-header' in str(response.content)
        assert 'class="fr-footer' in str(response.content)
        assert (
            "Retrouvez les bonnes adresses sur <a "
            'href="https://longuevieauxobjets.ademe.fr/" target="_blank" rel="noopener"'
            ">longuevieauxobjets.ademe.fr</a>" not in str(response.content)
        )
