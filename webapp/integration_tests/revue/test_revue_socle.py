import json

import pytest
from django.contrib.auth.models import User

API_ME = "/api/suggestions/me"
PAGE = "/data/revue/"


@pytest.fixture
def superuser():
    return User.objects.create_user(username="revue-admin", is_superuser=True)


@pytest.fixture
def staff():
    return User.objects.create_user(username="revue-staff", is_staff=True)


@pytest.mark.django_db
class TestApiAuth:
    def test_anonymous_is_unauthorized(self, client):
        assert client.get(API_ME).status_code == 401

    def test_non_superuser_is_forbidden(self, client, staff):
        client.force_login(staff)

        response = client.get(API_ME)

        assert response.status_code == 403

    def test_superuser_is_allowed(self, client, superuser):
        client.force_login(superuser)

        response = client.get(API_ME)

        assert response.status_code == 200
        assert response.json() == {"id": superuser.id, "username": "revue-admin"}


@pytest.mark.django_db
class TestPage:
    def test_anonymous_is_redirected_to_admin_login(self, client):
        response = client.get(PAGE)

        assert response.status_code == 302
        assert response.url.startswith("/admin/login/")

    def test_non_superuser_is_forbidden(self, client, staff):
        client.force_login(staff)

        assert client.get(PAGE).status_code == 403

    @pytest.mark.parametrize("path", [PAGE, f"{PAGE}cohortes/12?vue=lignes"])
    def test_superuser_gets_the_shell_page(self, client, superuser, path):
        client.force_login(superuser)

        response = client.get(path)

        assert response.status_code == 200
        assert 'id="revue-root"' in response.content.decode()
        assert "csrftoken" in response.cookies
        bootstrap = json.loads(
            response.content.decode()
            .split('<script id="revue-bootstrap" type="application/json">')[1]
            .split("</script>")[0]
        )
        assert bootstrap["basepath"] == PAGE
        assert bootstrap["apiBase"] == "/api/suggestions"
        assert bootstrap["user"]["username"] == "revue-admin"

    def test_existing_data_urls_are_still_served(self, client, superuser):
        client.force_login(superuser)

        # The review include must not shadow the existing data/ routes
        response = client.get("/data/suggestion-groupe/0/")

        assert response.status_code == 404
        assert b"revue-root" not in response.content
