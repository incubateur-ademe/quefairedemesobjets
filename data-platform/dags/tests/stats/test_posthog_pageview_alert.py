import pytest
from airflow.exceptions import AirflowException
from dags.stats.dags.posthog_pageview_alert import check_pageviews


def test_check_pageviews_raises_below_threshold():
    with pytest.raises(AirflowException, match="seulement 9"):
        check_pageviews(9, 10)


def test_check_pageviews_passes_at_threshold():
    check_pageviews(10, 10)
