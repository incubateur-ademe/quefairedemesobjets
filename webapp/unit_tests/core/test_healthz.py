import pytest


@pytest.mark.django_db
class TestHealthz:
    def test_healthz_returns_ok(self, client):
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.text == "ok"
