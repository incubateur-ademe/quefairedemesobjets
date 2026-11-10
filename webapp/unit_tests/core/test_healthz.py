import pytest


@pytest.mark.django_db
class TestHealthz:
    def test_healthz_returns_ok(self, client):
        response = client.get("/healthz/")
        assert response.status_code == 200
        assert response.text == "ok"

    def test_healthz_accepts_the_probe_host(self, client):
        # Scaleway's probe sends the container's internal IP as Host, which is
        # in no ALLOWED_HOSTS.
        response = client.get("/healthz/", HTTP_HOST="100.96.3.4:8000")
        assert response.status_code == 200

    def test_healthz_is_never_cached(self, client):
        # A cached "ok" in nginx would hide a dead gunicorn from the probe.
        response = client.get("/healthz/")
        assert "no-store" in response["Cache-Control"]
