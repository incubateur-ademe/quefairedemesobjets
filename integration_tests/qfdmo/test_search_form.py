import pytest
from bs4 import BeautifulSoup
from django.core.management import call_command


@pytest.fixture(scope="session")
def populate_admin_object(django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            "categories",
            "actions",
            "acteur_services",
            "acteur_types",
        )


@pytest.mark.django_db
class TestDirectionOrder:
    @pytest.mark.parametrize(
        "params,expected_order",
        [
            ("", ["jai", "jecherche"]),
            ("?first_dir=fake", ["jai", "jecherche"]),
            ("?first_dir=jai", ["jai", "jecherche"]),
            ("?first_dir=jecherche", ["jecherche", "jai"]),
        ],
    )
    def test_default_direction(self, client, params, expected_order):
        url = params

        response = client.get(url)
        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")
        input_tags = soup.find_all("input", {"name": "direction"})
        assert len(input_tags) == 2
        assert input_tags[0]["value"] == expected_order[0]
        assert input_tags[1]["value"] == expected_order[1]


@pytest.mark.django_db
class TestDirectionChecked:
    @pytest.mark.parametrize(
        "params,checked_direction",
        [
            ("", "jai"),
            ("?direction=fake", "jai"),
            ("?direction=jai", "jai"),
            ("?direction=jecherche", "jecherche"),
        ],
    )
    def test_default_direction(self, client, params, checked_direction):
        url = params

        response = client.get(url)
        assert response.status_code == 200

        soup = BeautifulSoup(response.content, "html.parser")
        input_tag = soup.find(
            "input", {"name": "direction", "value": checked_direction}
        )
        assert input_tag is not None
        assert "checked" in input_tag.attrs
