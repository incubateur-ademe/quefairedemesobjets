from datetime import datetime, timezone

import requests
from django.conf import settings
from ninja import Query, Router
from ninja.errors import HttpError

from stats.query import QUERY_DATA
from stats.schemas import Stat, StatInput, StatOutput, StatPeriodicity
from stats.utils import floor_to_period, parse_date, shift_period

router = Router(tags=["Stats"])

DESCRIPTION = (
    "Visiteurs orientés : visiteurs ayant consultés une page d'un produit "
    "ou ayant fait une recherche sur la carte"
)


def fetch_north_star_stats(
    periodicity: StatPeriodicity,
    *,
    since: int | None = None,
) -> StatOutput:

    def _get_stat_setting(name: str) -> str:
        value = settings.STATS.get(name)
        if not value:
            raise RuntimeError(f"Le paramètre {name} n'est pas configuré.")
        return value

    def _build_query_payload(
        periodicity: StatPeriodicity, since: int | None = None
    ) -> dict:
        query_payload = QUERY_DATA.copy()
        query_payload["query"]["interval"] = periodicity
        if since:
            start = shift_period(now, periodicity, -(since - 1))
            query_payload["query"]["dateRange"]["date_from"] = start.isoformat()
        return query_payload

    def _execute_query(
        query_url: str, query_payload: dict, headers: dict
    ) -> list[dict]:
        try:
            response = requests.post(
                query_url, json=query_payload, headers=headers, timeout=10
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise HttpError(502, "Impossible d'exécuter la query PostHog.") from exc

        body = response.json()
        results = body.get("results") or []
        if not results:
            raise HttpError(502, "PostHog ne renvoie aucune donnée.")
        return results

    def _format_results(results: list[dict]) -> list[Stat]:
        first = results[0]
        # Les dates sont au format "YYYY-MM-DD" dans le champ "days"
        days = first.get("days") or []
        # Les valeurs sont dans le champ "data"
        values = first.get("data") or []

        if len(days) != len(values):
            raise HttpError(
                502, "Les données PostHog sont incohérentes (dates/valeurs)."
            )

        # Parser les dates et créer un dictionnaire date -> valeur
        values_by_date: dict[datetime, float] = {}
        for day_str, value in zip(days, values):
            date = parse_date(day_str)
            # S'assurer que la date est au début de la période demandée
            date = floor_to_period(date, periodicity)
            values_by_date[date] = int(value or 0)

        stats = [
            Stat(date=int(point.timestamp()), iso_date=point.isoformat(), value=value)
            for point, value in sorted(values_by_date.items())
        ]
        return stats

    # Settings
    now = datetime.now(timezone.utc)
    base_url = _get_stat_setting("POSTHOG_BASE_URL").rstrip("/")
    project_id = _get_stat_setting("POSTHOG_PROJECT_ID")
    api_key = _get_stat_setting("POSTHOG_PERSONAL_API_KEY")

    # Execute query
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    query_url = f"{base_url}/api/projects/{project_id}/query/"
    query_payload = _build_query_payload(periodicity, since)
    results = _execute_query(query_url, query_payload, headers)

    # Format results
    stats = _format_results(results)

    return StatOutput(description=DESCRIPTION, stats=stats)


@router.get("", response=StatOutput, summary="Statistiques publiques")
def stats_endpoint(request, query: StatInput = Query(...)):  # type: ignore[assignment]
    return fetch_north_star_stats(query.periodicity, since=query.since)
