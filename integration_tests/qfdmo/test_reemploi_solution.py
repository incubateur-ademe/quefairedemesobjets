import pytest
from django.conf import settings
from django.core.management import call_command


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command(
            "loaddata",
            "categories",
            "actions",
            "acteur_services",
            "acteur_types",
        )


@pytest.mark.django_db
class TestInitialValue:

    default_context = {
        "sous_categorie_objet": None,
        "sc_id": None,
        "adresse": None,
        "direction": settings.DEFAULT_ACTION_DIRECTION,
        "digital": "0",
        "latitude": None,
        "longitude": None,
        "label_reparacteur": None,
        "ess": None,
        "bonus": None,
        "bounding_box": None,
        "pas_exclusivite_reparation": True,
        "action_displayed": (
            "preter|emprunter|louer|mettreenlocation|reparer|donner|echanger"
            "|acheter|revendre"
        ),
        "action_list": (
            "preter|emprunter|louer|mettreenlocation|reparer|donner|echanger"
            "|acheter|revendre"
        ),
        "epci_codes": [],
    }

    def test_no_parameters(self, client):
        url = ""
        response = client.get(url)

        assert response.status_code == 200
        assert response.context_data["location"] == "{}"
        assert response.context_data["acteurs"].count() == 0
        assert response.context_data["form"].initial == self.default_context

    def test_carte(self, client):
        url = "?carte"

        response = client.get(url)

        assert response.status_code == 200
        assert response.context_data["location"] == "{}"
        assert response.context_data["acteurs"].count() == 0
        assert response.context_data["form"].initial == {
            **self.default_context,
            "direction": None,
            "action_displayed": (
                "preter|emprunter|louer|mettreenlocation|reparer|donner|echanger"
                "|acheter|revendre|trier"
            ),
            "action_list": (
                "reparer|donner|echanger|preter|emprunter|louer|mettreenlocation|"
                "acheter|revendre|trier"
            ),
            "grouped_action": [
                "reparer",
                "donner|echanger",
                "preter|emprunter|louer|mettreenlocation",
                "acheter|revendre",
                "trier",
            ],
            "legend_grouped_action": [
                "reparer",
                "donner|echanger",
                "preter|emprunter|louer|mettreenlocation",
                "acheter|revendre",
                "trier",
            ],
        }

    def test_iframe(self, client):
        url = "?iframe"

        response = client.get(url)

        assert response.status_code == 200
        assert response.context_data["location"] == "{}"
        assert response.context_data["acteurs"].count() == 0
        assert response.context_data["form"].initial == self.default_context
