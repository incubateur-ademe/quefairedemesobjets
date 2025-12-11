import pytest
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
        "adresse": None,
        "latitude": None,
        "longitude": None,
        "bounding_box": None,
    }

    def test_formulaire_without_parameters(self, client):
        url = "/formulaire"

        response = client.get(url)

        assert response.status_code == 200
        assert response.context_data["location"] == ""
        assert len(response.context_data["acteurs"]) == 0
        assert response.context_data["form"].initial == {
            **self.default_context,
            "action_displayed": "preter|emprunter|louer|mettreenlocation"
            "|reparer|donner|echanger|acheter|revendre",
            "action_list": "preter|emprunter|louer|mettreenlocation|"
            "reparer|donner|echanger|acheter|revendre",
            "bonus": None,
            "ess": None,
            "label_reparacteur": None,
            "pas_exclusivite_reparation": True,
            "sc_id": None,
            "sous_categorie_objet": None,
        }

    def test_carte_without_parameters(self, client):
        url = "/carte"

        response = client.get(url)

        assert response.status_code == 200
        assert response.context_data["location"] == ""
        assert len(response.context_data["acteurs"]) == 0
        assert response.context_data["form"].initial == self.default_context
