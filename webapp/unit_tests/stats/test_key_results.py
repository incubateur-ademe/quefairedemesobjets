from datetime import date
from unittest.mock import Mock, patch

import pytest
from django.db import connection
from django.urls import reverse

from stats.key_results import REGISTRY, compute_all, part_acteurs_siret_siren
from stats.models import KeyResult, KeyResultValue
from stats.posthog import run_insight

pytestmark = pytest.mark.django_db


def current(code):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_value, progress, last_date FROM stats_keyresult_current"
            " WHERE code = %s",
            [code],
        )
        return cursor.fetchone()


def test_compute_all_upserts_code_and_posthog_sources_and_skips_manual():
    KeyResult.objects.all().delete()
    KeyResult.objects.create(code="kr", source="code")
    posthog = KeyResult.objects.create(
        code="ph", source="posthog", posthog_insight="abc"
    )
    KeyResult.objects.create(code="manual", source="manual")
    KeyResultValue.objects.create(key_result=posthog, date=date(2026, 1, 1), value=1)

    with (
        patch.dict(REGISTRY, {"kr": lambda: {date(2026, 1, 1): 1.0}}, clear=True),
        patch("stats.key_results.run_insight", return_value={date(2026, 1, 1): 5.0}),
    ):
        assert compute_all() == 2

    assert list(KeyResultValue.objects.values_list("key_result__code", "value")) == [
        ("kr", 1.0),
        ("ph", 5.0),
    ]


def test_compute_all_skips_a_failing_key_result():
    KeyResult.objects.all().delete()
    KeyResult.objects.create(code="broken", source="posthog", posthog_insight="x")
    KeyResult.objects.create(code="kr", source="code")

    with (
        patch("stats.key_results.run_insight", side_effect=ValueError("boom")),
        patch.dict(REGISTRY, {"kr": lambda: {date(2026, 1, 1): 1.0}}, clear=True),
    ):
        assert compute_all() == 1


def test_current_view_sums_the_year_or_takes_the_last_value():
    this_year = date.today().year
    summed = KeyResult.objects.create(code="s", aggregation="sum_year", target=10)
    last = KeyResult.objects.create(code="l", aggregation="last")
    empty = KeyResult.objects.create(code="e", aggregation="sum_year", target=10)
    for day, value in [
        (date(this_year - 1, 12, 1), 100),
        (date(this_year, 1, 1), 2),
        (date(this_year, 2, 1), 3),
    ]:
        KeyResultValue.objects.create(key_result=summed, date=day, value=value)
        KeyResultValue.objects.create(key_result=last, date=day, value=value)

    assert current("s") == (5.0, 0.5, date(this_year, 2, 1))
    assert current("l") == (3.0, None, date(this_year, 2, 1))
    assert current("e") == (None, None, None)
    assert empty.pk


def test_part_acteurs_siret_siren_excludes_source_and_short_ids():
    from unit_tests.qfdmo.acteur_factory import DisplayedActeurFactory, SourceFactory

    excluded = SourceFactory(code="recyclivrebal")
    DisplayedActeurFactory(siret="12345678901234")
    DisplayedActeurFactory(siren="", siret="123")
    DisplayedActeurFactory(siret="12345678901234", source=excluded)

    values = part_acteurs_siret_siren()

    assert list(values.values()) == [0.5]
    assert list(values)[0].day == 1


@patch("stats.posthog.requests.request")
def test_run_insight_runs_the_saved_query_monthly_and_keeps_the_first_series(
    mock_request, settings
):
    settings.STATS = {
        "POSTHOG_BASE_URL": "https://eu.posthog.com",
        "POSTHOG_PROJECT_ID": "1",
        "POSTHOG_PERSONAL_API_KEY": "k",  # pragma: allowlist secret
    }
    insight = {
        "results": [
            {"query": {"kind": "InsightVizNode", "source": {"kind": "TrendsQuery"}}}
        ]
    }
    run = {
        "results": [
            {"days": ["2026-01-01", "2026-02-01"], "data": [10, None]},
            {"days": ["2026-01-01"], "data": [99]},
        ]
    }
    mock_request.side_effect = [Mock(json=lambda: insight), Mock(json=lambda: run)]

    assert run_insight("abc") == {date(2026, 1, 1): 10.0, date(2026, 2, 1): 0.0}
    assert mock_request.call_args.kwargs["json"] == {
        "query": {"kind": "TrendsQuery", "interval": "month"}
    }


def test_key_results_are_managed_in_wagtail(admin_client):
    with patch("stats.posthog.list_insights", return_value=[("abc", "Visiteurs")]):
        listing = admin_client.get(reverse("wagtailsnippets_stats_keyresult:list"))
        form = admin_client.get(reverse("wagtailsnippets_stats_keyresult:add"))

    assert listing.status_code == 200
    assert "visiteurs_orientes" in listing.content.decode()
    assert 'value="abc"' in form.content.decode()
