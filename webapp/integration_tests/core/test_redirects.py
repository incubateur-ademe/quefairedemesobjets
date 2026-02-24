import pytest
from django.test import override_settings

# from core.views import static_file_content_from


@pytest.mark.django_db
@override_settings(DEBUG=False)
@pytest.mark.parametrize(
    "test_url",
    ["/configurateur", "/sitemap.xml"],
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
        # Carte
        # Assistant
        ("quefairedemesdechets.ademe.fr", "/", None, 200),
        ("quefairedemesdechets.ademe.fr", "/carte", None, 200),
        (
            "quefairedemesdechets.ademe.fr",
            "?formulaire",
            "https://quefairedemesdechets.ademe.fr/formulaire",
            301,
        ),
        (
            "quefairedemesdechets.ademe.fr",
            "?iframe&direction=jai",
            "https://quefairedemesdechets.ademe.fr/formulaire?direction=jai",
            301,
        ),
        (
            "quefairedemesdechets.ademe.fr",
            "?carte",
            "https://quefairedemesdechets.ademe.fr/carte",
            301,
        ),
        # Integrations from Notion list
        (
            "quefairedemesdechets.ademe.fr",
            "/carte?action_list=reparer%7Cdonner%7Cechanger%7Crapporter%7Cpreter%7Cemprunter%7Clouer%7Cmettreenlocation%7Cacheter%7Crevendre%7Ctrier&epci_codes=243100518&epci_codes=200071314&epci_codes=243100732&epci_codes=243100773&epci_codes=243100633&epci_codes=243100781&epci_codes=200034957&epci_codes=243100815&limit=50",
            None,
            200,
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


# Temporarily disable this test as scripts are not available in CI.
# This should be fixed in the future (27 august 2025)
# def ztest_scripts(
#     client,
# ):
#     assert (
#         client.get("/iframe.js").content
#         == static_file_content_from("embed/assistant.js").content
#     )
#     assert (
#         client.get("/static/iframe.js").content
#         == static_file_content_from(
#             "embed/formulaire.js",
#         ).content
#     )
#     assert (
#         client.get("/static/carte.js").content
#         == static_file_content_from("embed/carte.js").content
#     )
