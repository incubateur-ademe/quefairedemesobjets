from types import SimpleNamespace

import pytest
from airflow.exceptions import AirflowException
from dags.stats.dags.posthog_pageview_alert import check_pageviews, mattermost_payload


def test_check_pageviews_raises_below_threshold():
    with pytest.raises(AirflowException, match="seulement 9"):
        check_pageviews(9, 10)


def test_check_pageviews_passes_at_threshold():
    check_pageviews(10, 10)


def test_mattermost_payload_targets_tour_de_controle():
    context = {
        "exception": AirflowException("boom"),
        "task_instance": SimpleNamespace(log_url="http://airflow/log"),
    }
    payload = mattermost_payload(context)
    assert payload["channel"] == "qfdmod-tour-de-controle"
    assert payload["text"] == "boom [Voir les logs](http://airflow/log)"
