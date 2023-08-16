import pytest


class TestDisplayAsIframe:
    @pytest.mark.django_db
    def test_display_as_iframe(self, client):
        url = "?iframe"

        response = client.get(url)

        assert response.status_code == 200
        assert 'class="fr-header' not in str(response.content)
        assert 'class="fr-footer' not in str(response.content)

    def test_display_as_no_iframe(self, client):
        url = ""

        response = client.get(url)

        assert response.status_code == 200
        assert 'class="fr-header' in str(response.content)
        assert 'class="fr-footer' in str(response.content)
