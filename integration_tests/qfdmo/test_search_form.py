import pytest
from django.core.management import call_command

from qfdmo.models import CachedDirectionAction


@pytest.fixture(scope="session")
def populate_admin_object(django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            "categories",
            "action_directions",
            "actions",
            "acteur_services",
            "acteur_types",
        )
        CachedDirectionAction.reload_cache()


@pytest.mark.django_db
class TestDirectionOrder:
    def test_default_direction(self, client):
        url = ""

        response = client.get(url)
        assert response.status_code == 200
        assert 'value="jai"' in str(response.content)
        assert 'value="jecherche"' in str(response.content)
        assert str(response.content).index('value="jai"') < str(response.content).index(
            'value="jecherche"'
        )

    def test_jai_first_direction(self, client):
        url = "?first_dir=jai"

        response = client.get(url)
        assert response.status_code == 200
        assert 'value="jai"' in str(response.content)
        assert 'value="jecherche"' in str(response.content)
        assert str(response.content).index('value="jai"') < str(response.content).index(
            'value="jecherche"'
        )

    def test_jecherche_first_direction(self, client):
        url = "?first_dir=jecherche"

        response = client.get(url)
        assert response.status_code == 200
        assert 'value="jai"' in str(response.content)
        assert 'value="jecherche"' in str(response.content)
        assert str(response.content).index('value="jai"') > str(response.content).index(
            'value="jecherche"'
        )
