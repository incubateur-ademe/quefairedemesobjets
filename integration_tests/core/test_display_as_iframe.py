import pytest
from django.core.management import call_command

from qfdmo.models import CachedDirectionAction


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            "actions",
        )
        CachedDirectionAction.reload_cache()


class TestDisplayAsIframe:
    @pytest.mark.django_db
    def test_display_as_iframe(self, client):
        url = "?iframe"

        response = client.get(url)
        print(response.content)
        assert response.status_code == 200
        assert 'class="fr-header' not in str(response.content)
        assert 'class="fr-footer' not in str(response.content)
        assert b"R\xc3\xa9utiliser cette carte sur mon site" in response.content
        assert b"Participer \xc3\xa0 son am\xc3\xa9lioration" in response.content
        assert "longuevieauxobjets.ademe.fr" in str(response.content)

    @pytest.mark.django_db
    def test_display_as_no_iframe(self, client):
        url = ""

        response = client.get(url)

        assert response.status_code == 200
        assert 'class="fr-header' in str(response.content)
        assert 'class="fr-footer' in str(response.content)
        assert "Pour en savoir plus :" not in str(response.content)
