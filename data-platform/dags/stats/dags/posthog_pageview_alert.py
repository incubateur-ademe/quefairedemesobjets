"""Alerte si PostHog reçoit moins de 10 $pageview par minute.

La tâche échoue quand le seuil n'est pas atteint, et envoie un
message mattermost.
"""

import logging
import os

import requests
from airflow.exceptions import AirflowException
from airflow.sdk import dag, task
from shared.config.airflow import DEFAULT_ARGS_NO_RETRIES
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS
from utils.django import django_setup_full

logger = logging.getLogger(__name__)

PAGEVIEW_THRESHOLD = 10
MATTERMOST_CHANNEL = "qfdmod-tour-de-controle"
MATTERMOST_USERNAME = "Bipboop le robot de seconde main"
MATTERMOST_ICON = (
    "https://cdn3.iconfinder.com/data/icons/system-basic-vol-4-1/20/"
    "icon-note-attention-alt3-512.png"
)

# fenêtre [now-2min, now-1min] pour absorber le délai d'ingestion PostHog
QUERY = """
SELECT count() FROM events
WHERE event = '$pageview'
  AND timestamp >= now() - INTERVAL 2 MINUTE
  AND timestamp <  now() - INTERVAL 1 MINUTE
"""


def posthog_pageview_count() -> int:
    django_setup_full()
    from django.conf import settings

    stats = settings.STATS
    base_url = stats["POSTHOG_BASE_URL"].rstrip("/")
    response = requests.post(
        f"{base_url}/api/projects/{stats['POSTHOG_PROJECT_ID']}/query/",
        json={"query": {"kind": "HogQLQuery", "query": QUERY}},
        headers={"Authorization": f"Bearer {stats['POSTHOG_PERSONAL_API_KEY']}"},
        timeout=20,
    )
    response.raise_for_status()
    return int(response.json()["results"][0][0])


def check_pageviews(count: int, threshold: int) -> None:
    if count < threshold:
        raise AirflowException(
            f"⚠️ PostHog : seulement {count} $pageview sur la dernière minute "
            f"(seuil {threshold})"
        )


def mattermost_payload(context: dict) -> dict:
    ti = context["task_instance"]
    return {
        "text": f"{context.get('exception')} [Voir les logs]({ti.log_url})",
        "channel": MATTERMOST_CHANNEL,
        "username": MATTERMOST_USERNAME,
        "icon": MATTERMOST_ICON,
    }


def notify_mattermost(context: dict) -> None:
    webhook_url = os.environ.get("MATTERMOST_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("MATTERMOST_WEBHOOK_URL absent : pas de notification")
        return
    requests.post(webhook_url, json=mattermost_payload(context), timeout=10)


@dag(
    dag_id="posthog_pageview_alert",
    dag_display_name="Stats - PostHog - Alerte si trop peu de pages vues",
    default_args=DEFAULT_ARGS_NO_RETRIES,
    schedule=SCHEDULES.EVERY_MINUTE,
    start_date=START_DATES.DEFAULT,
    catchup=False,
    is_paused_upon_creation=False,
    max_active_runs=1,
    tags=[TAGS.STATS, TAGS.MAINTENANCE],
)
def posthog_pageview_alert():
    @task(on_failure_callback=notify_mattermost)
    def check():
        check_pageviews(posthog_pageview_count(), PAGEVIEW_THRESHOLD)

    check()


posthog_pageview_alert()
