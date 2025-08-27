import pytest
from django.test import override_settings


@pytest.mark.django_db
@override_settings(DEBUG=False)
@pytest.mark.parametrize(
    "test_url",
    ["/configurateur", "/sitemap.xml", "/dsfr/colors"],
)
def test_other_routes_work(client, test_url):
    response = client.get(test_url)
    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(DEBUG=False)
@pytest.mark.parametrize(
    "test_url",
    [
        "/donnez-votre-avis",
        "/proposer-une-adresse",
        "/proposer-une-modification",
        "/nous-contacter",
    ],
)
def test_forms_redirects(client, test_url):
    response = client.get(test_url)
    assert response.status_code == 301


@pytest.mark.django_db
@override_settings(
    ALLOWED_HOSTS=[
        "quefairedemesdechets.ademe.fr",
        "lvao.ademe.fr",
        "quefairedemesobjets.ademe.fr",
    ],
    BASE_URL="https://quefairedemesdechets.ademe.fr",
)
@pytest.mark.parametrize(
    "host,url,expected_url,expected_status_code",
    [
        # Redirects to CMS
        ("lvao.ademe.fr", "", "https://quefairedemesdechets.ademe.fr/", 301),
        ("lvao.ademe.fr", "/", "https://quefairedemesdechets.ademe.fr/", 301),
        # Épargnons, Formulaire
        (
            "lvao.ademe.fr",
            "/formulaire",
            "https://quefairedemesdechets.ademe.fr/formulaire",
            301,
        ),
        # Carte
        ("lvao.ademe.fr", "/carte", "https://quefairedemesdechets.ademe.fr/carte", 301),
        # Scripts
        (
            "lvao.ademe.fr",
            "/static/iframe.js",
            "https://quefairedemesdechets.ademe.fr/static/iframe.js",
            301,
        ),
        (
            "lvao.ademe.fr",
            "/static/carte.js",
            "https://quefairedemesdechets.ademe.fr/static/carte.js",
            301,
        ),
        # Assistant
        ("quefairedemesdechets.ademe.fr", "/", None, 200),
        ("quefairedemesdechets.ademe.fr", "/carte", None, 200),
        (
            "quefairedemesdechets.ademe.fr",
            "/static/iframe.js",
            None,
            200,
        ),  # formulaire script
        (
            "quefairedemesdechets.ademe.fr",
            "/static/carte.js",
            None,
            200,
        ),  # carte script
        ("quefairedemesdechets.ademe.fr", "/iframe.js", None, 200),  # assistant script
        ("lvao.ademe.fr", "?carte", "https://quefairedemesdechets.ademe.fr/carte", 301),
        (
            "lvao.ademe.fr",
            "?formulaire",
            "https://quefairedemesdechets.ademe.fr/formulaire",
            301,
        ),
        (
            "lvao.ademe.fr",
            "?iframe&direction=jai",
            "https://quefairedemesdechets.ademe.fr/formulaire?direction=jai",
            301,
        ),
        (
            "lvao.ademe.fr",
            "/?carte",
            "https://quefairedemesdechets.ademe.fr/carte",
            301,
        ),
        # Integrations from Notion list
        (
            "lvao.ademe.fr",
            "/carte?action_list=reparer%7Cdonner%7Cechanger%7Crapporter%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cacheter%7Crevendre%7Ctrier&epci_codes=243100518&epci_codes=200071314&epci_codes=243100732&epci_codes=243100773&epci_codes=243100633&epci_codes=243100781&epci_codes=200034957&epci_codes=243100815&limit=50",
            "https://quefairedemesdechets.ademe.fr/carte?action_list=reparer%7Cdonner%7Cechanger%7Crapporter%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cacheter%7Crevendre%7Ctrier&epci_codes=243100518&epci_codes=200071314&epci_codes=243100732&epci_codes=243100773&epci_codes=243100633&epci_codes=243100781&epci_codes=200034957&epci_codes=243100815&limit=50",
            301,
        ),
        (
            "quefairedemesdechets.ademe.fr",
            "/carte?action_list=reparer%7Cdonner%7Cechanger%7Crapporter%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cacheter%7Crevendre%7Ctrier&epci_codes=243100518&epci_codes=200071314&epci_codes=243100732&epci_codes=243100773&epci_codes=243100633&epci_codes=243100781&epci_codes=200034957&epci_codes=243100815&limit=50",
            None,
            200,
        ),
        (
            "lvao.ademe.fr",
            "/carte?action_list=preter%7Cemprunter%7Clouer%7Cmettreenlocation%7Creparer%7Cdonner%7Cechanger%7Cacheter%7Crevendre%7Crapporter&bounding_box=%7B%22southWest%22%3A%7B%22lat%22%3A48.803292%2C%22lng%22%3A2.41289%7D%2C%22northEast%22%3A%7B%22lat%22%3A48.941676%2C%22lng%22%3A2.598727%7D%7D",
            "https://quefairedemesdechets.ademe.fr/carte?action_list=preter%7Cemprunter%7Clouer%7Cmettreenlocation%7Creparer%7Cdonner%7Cechanger%7Cacheter%7Crevendre%7Crapporter&bounding_box=%7B%22southWest%22%3A%7B%22lat%22%3A48.803292%2C%22lng%22%3A2.41289%7D%2C%22northEast%22%3A%7B%22lat%22%3A48.941676%2C%22lng%22%3A2.598727%7D%7D",
            301,
        ),
        (
            "quefairedemesdechets.ademe.fr",
            "/carte?action_list=preter%7Cemprunter%7Clouer%7Cmettreenlocation%7Creparer%7Cdonner%7Cechanger%7Cacheter%7Crevendre%7Crapporter&bounding_box=%7B%22southWest%22%3A%7B%22lat%22%3A48.803292%2C%22lng%22%3A2.41289%7D%2C%22northEast%22%3A%7B%22lat%22%3A48.941676%2C%22lng%22%3A2.598727%7D%7D",
            None,
            200,
        ),
    ],
)
def test_redirects(
    client,
    host,
    url,
    expected_url,
    expected_status_code,
):
    response = client.get(url, headers={"Host": host})
    assert response.status_code == expected_status_code
    if expected_url:
        assert response.url == expected_url
