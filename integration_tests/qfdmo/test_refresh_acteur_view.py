import pytest


class TestRefreshActorView:
    @pytest.mark.django_db
    def test_command_is_called(self, client):
        url = "/qfdmo/refresh_acteur_view"
        response = client.get(url, HTTP_REFERER="http://example.com")
        assert response.status_code == 302
        assert response["Location"] == "http://localhost:8080"
