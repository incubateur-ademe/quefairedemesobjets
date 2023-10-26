from unittest.mock import patch

import pytest

from qfdmo.thread.materialized_view import RefreshMateriazedViewThread


class TestRefreshActorView:
    @pytest.mark.django_db
    def test_command_is_called(self, client):
        with patch.object(
            RefreshMateriazedViewThread, "run", return_value=None
        ) as mock_method:
            url = "/qfdmo/refresh_acteur_view"
            response = client.get(url, HTTP_REFERER="http://example.com")
            assert response.status_code == 302
            mock_method.assert_called_once()
