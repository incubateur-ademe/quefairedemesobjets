import pytest
from django.core.management import call_command


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            "actions",
        )


class TestDisplayAsIframe:
    @pytest.mark.django_db
    def test_display_as_iframe(self, client):
        url = "/formulaire"
        response = client.get(url)
        assert response.status_code == 200
        assert 'class="fr-header' not in str(response.content)
        assert 'class="fr-footer' not in str(response.content)
        assert b"R\xc3\xa9utiliser cette carte sur mon site" in response.content
        assert b"Participer \xc3\xa0 son am\xc3\xa9lioration" in response.content
        assert "longuevieauxobjets.ademe.fr" in str(response.content)
