from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from django.test import override_settings
from ninja.errors import HttpError
from urllib.parse import urlparse
from stats.api import fetch_north_star_stats

# Fixtures
# --------
# PostHog configuration for tests
MOCK_POSTHOG_SETTINGS = {
    "POSTHOG_BASE_URL": "https://eu.posthog.com",
    "POSTHOG_PROJECT_ID": "12345",
    "POSTHOG_PERSONAL_API_KEY": "test-api-key",  # pragma: allowlist secret
}


@pytest.fixture
def mock_posthog_response_daily():
    """Fixture for a successful PostHog response with data"""
    return {
        "results": [
            {
                "days": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "data": [10, 15, 20],
            }
        ]
    }


@pytest.fixture
def mock_posthog_response_weekly():
    """Fixture for a PostHog response with weekly data"""
    return {
        "results": [
            {
                "days": ["2024-01-01", "2024-01-08", "2024-01-15"],
                "data": [100, 150, 200],
            }
        ]
    }


@pytest.fixture
def mock_posthog_response_monthly():
    """Fixture for a PostHog response with monthly data"""
    return {
        "results": [
            {
                "days": ["2024-01-01", "2024-02-01", "2024-03-01"],
                "data": [1000, 1500, 2000],
            }
        ]
    }


class TestFetchNorthStarStats:
    @override_settings(STATS={"POSTHOG_BASE_URL": "https://eu.posthog.com"})
    def test_missing_settings_raises_runtime_error(self):
        """Test that missing configuration raises a RuntimeError"""
        with pytest.raises(RuntimeError, match="Le paramètre POSTHOG_PROJECT_ID"):
            fetch_north_star_stats("day", since=None)

    @override_settings(
        STATS={
            "POSTHOG_BASE_URL": "https://eu.posthog.com",
            "POSTHOG_PROJECT_ID": "12345",
        }
    )
    def test_missing_api_key_raises_runtime_error(self):
        with pytest.raises(RuntimeError, match="Le paramètre POSTHOG_PERSONAL_API_KEY"):
            fetch_north_star_stats("day", since=None)

    @override_settings(STATS=MOCK_POSTHOG_SETTINGS)
    @patch("stats.api.requests.post")
    def test_success_with_daily_periodicity(
        self, mock_post, mock_posthog_response_daily
    ):
        """Test a successful call with daily periodicity"""
        # Mock configuration
        mock_response = Mock()
        mock_response.json.return_value = mock_posthog_response_daily
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Execution
        result = fetch_north_star_stats("day", since=None)

        # Assertions
        assert result.description is not None
        assert len(result.stats) == 3
        assert result.stats[0].value == 10
        assert result.stats[1].value == 15
        assert result.stats[2].value == 20
        assert all(stat.date > 0 for stat in result.stats)
        assert all(stat.iso_date for stat in result.stats)

        # API call verification
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        # Parse URL and confirm hostname matches expected
        url = call_args[0][0]
        hostname = urlparse(url).hostname
        assert hostname == "eu.posthog.com"
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-api-key"
        assert call_args[1]["json"]["query"]["interval"] == "day"

    @override_settings(STATS=MOCK_POSTHOG_SETTINGS)
    @patch("stats.api.requests.post")
    def test_success_with_weekly_periodicity(
        self, mock_post, mock_posthog_response_weekly
    ):
        """Test a successful call with weekly periodicity"""
        mock_response = Mock()
        mock_response.json.return_value = mock_posthog_response_weekly
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = fetch_north_star_stats("week", since=None)

        assert len(result.stats) == 3
        assert result.stats[0].value == 100
        call_args = mock_post.call_args
        assert call_args[1]["json"]["query"]["interval"] == "week"

    @override_settings(STATS=MOCK_POSTHOG_SETTINGS)
    @patch("stats.api.requests.post")
    def test_success_with_monthly_periodicity(
        self, mock_post, mock_posthog_response_monthly
    ):
        """Test a successful call with monthly periodicity"""
        mock_response = Mock()
        mock_response.json.return_value = mock_posthog_response_monthly
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = fetch_north_star_stats("month", since=None)

        assert len(result.stats) == 3
        assert result.stats[0].value == 1000
        call_args = mock_post.call_args
        assert call_args[1]["json"]["query"]["interval"] == "month"

    @override_settings(STATS=MOCK_POSTHOG_SETTINGS)
    @patch("stats.api.requests.post")
    def test_success_with_since_parameter(self, mock_post, mock_posthog_response_daily):
        """Test a successful call with the since parameter"""
        mock_response = Mock()
        mock_response.json.return_value = mock_posthog_response_daily
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        fetch_north_star_stats("day", since=7)

        # Verify that date_from is present in the payload
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert "date_from" in payload["query"]["dateRange"]

    @override_settings(STATS=MOCK_POSTHOG_SETTINGS)
    @patch("stats.api.requests.post")
    def test_success_with_base_url_trailing_slash(
        self, mock_post, mock_posthog_response_daily
    ):
        """Test that base URL without trailing slash works correctly"""
        # Configuration with trailing slash
        with override_settings(
            STATS={
                **MOCK_POSTHOG_SETTINGS,
                "POSTHOG_BASE_URL": "https://eu.posthog.com/",
            }
        ):
            mock_response = Mock()
            mock_response.json.return_value = mock_posthog_response_daily
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            fetch_north_star_stats("day", since=None)

            # Verify that the URL does not contain a double slash
            call_args = mock_post.call_args
            url = call_args[0][0]
            assert "//api" not in url
            assert url.endswith("/api/projects/12345/query/")

    @override_settings(STATS=MOCK_POSTHOG_SETTINGS)
    @patch("stats.api.requests.post")
    def test_http_error_raises_http_error(self, mock_post):
        """Test that an HTTP error raises an HttpError"""
        import requests

        mock_post.side_effect = requests.RequestException("Connection error")

        with pytest.raises(HttpError) as exc_info:
            fetch_north_star_stats("day", since=None)

        assert exc_info.value.status_code == 502
        assert "Impossible d'exécuter la query PostHog" in str(exc_info.value)

    @override_settings(STATS=MOCK_POSTHOG_SETTINGS)
    @patch("stats.api.requests.post")
    @pytest.mark.parametrize("return_value", [{}, {"results": []}])
    def test_empty_results_raises_http_error(self, mock_post, return_value):
        """Test that an empty response raises an HttpError"""
        mock_response = Mock()
        mock_response.json.return_value = return_value
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with pytest.raises(HttpError) as exc_info:
            fetch_north_star_stats("day", since=None)

        assert exc_info.value.status_code == 502
        assert "PostHog ne renvoie aucune donnée" in str(exc_info.value)

    @override_settings(STATS=MOCK_POSTHOG_SETTINGS)
    @patch("stats.api.requests.post")
    def test_incoherent_data_raises_http_error(self, mock_post):
        """Test that incoherent data (dates/values) raises an HttpError"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "days": ["2024-01-01", "2024-01-02"],
                    "data": [10],  # Fewer values than dates
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with pytest.raises(HttpError) as exc_info:
            fetch_north_star_stats("day", since=None)

        assert exc_info.value.status_code == 502
        assert "incohérentes" in str(exc_info.value)

    @override_settings(STATS=MOCK_POSTHOG_SETTINGS)
    @patch("stats.api.requests.post")
    def test_null_values_handled_correctly(self, mock_post):
        """Test that null values are treated as 0"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "days": ["2024-01-01", "2024-01-02"],
                    "data": [10, None],
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = fetch_north_star_stats("day", since=None)

        assert len(result.stats) == 2
        assert result.stats[0].value == 10
        assert result.stats[1].value == 0

    @override_settings(STATS=MOCK_POSTHOG_SETTINGS)
    @patch("stats.api.requests.post")
    def test_stats_sorted_by_date(self, mock_post):
        """Test that statistics are sorted by date"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "days": ["2024-01-03", "2024-01-01", "2024-01-02"],
                    "data": [30, 10, 20],
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = fetch_north_star_stats("day", since=None)

        assert len(result.stats) == 3
        # Verify that dates are sorted
        dates = [stat.date for stat in result.stats]
        assert dates == sorted(dates)
        # Verify that values correspond to the correct dates
        assert result.stats[0].value == 10  # 2024-01-01
        assert result.stats[1].value == 20  # 2024-01-02
        assert result.stats[2].value == 30  # 2024-01-03

    @override_settings(STATS=MOCK_POSTHOG_SETTINGS)
    @patch("stats.api.requests.post")
    def test_floor_to_period_applied(self, mock_post):
        """Test that floor_to_period is applied correctly"""
        # Data with hours/minutes to test the floor
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "days": ["2024-01-19"],  # A Wednesday
                    "data": [100],
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = fetch_north_star_stats("week", since=None)

        assert len(result.stats) == 1
        # The date should be the start of the week (Monday)
        stat_date = datetime.fromtimestamp(result.stats[0].date, tz=timezone.utc)
        assert stat_date.weekday() == 0  # Monday = 0
