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
        # When no location is provided, location should be empty string
        assert response.context_data["location"] == ""
        assert len(response.context_data["acteurs"]) == 0

        # Check form initial values
        # Formulaire uses the old form structure with form (not forms dict)
        form = response.context_data["form"]
        assert form.initial["adresse"] is None
        assert form.initial["latitude"] is None
        assert form.initial["longitude"] is None
        assert form.initial["bounding_box"] is None
        assert form.initial["action_displayed"] == (
            "preter|emprunter|louer|mettreenlocation"
            "|reparer|donner|echanger|acheter|revendre"
        )
        assert form.initial["action_list"] == (
            "preter|emprunter|louer|mettreenlocation|"
            "reparer|donner|echanger|acheter|revendre"
        )
        assert form.initial["bonus"] is None
        assert form.initial["ess"] is None
        assert form.initial["label_reparacteur"] is None
        assert form.initial["pas_exclusivite_reparation"] is True
        assert form.initial["sc_id"] is None
        assert form.initial["sous_categorie_objet"] is None

    def test_carte_without_parameters(self, client):
        url = "/carte"

        response = client.get(url)

        assert response.status_code == 200
        # When no location is provided, location should be empty string
        assert response.context_data["location"] == ""
        assert len(response.context_data["acteurs"]) == 0

        # Check map form initial values
        forms = response.context_data["forms"]
        assert forms["map"]["adresse"].value() is None
        assert forms["map"]["latitude"].value() is None
        assert forms["map"]["longitude"].value() is None
        assert forms["map"]["bounding_box"].value() is None
