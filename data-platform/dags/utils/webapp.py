"""Utilities to fetch webapp data through its HTTP API.

Used at DAG parse time instead of the Django ORM so the DAG processor
doesn't pay the cost of django.setup() + DB connections on every parse
(which caused DagBag import timeouts, see
https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#top-level-python-code)
"""

import functools

import requests
from decouple import config

TIMEOUT_SECONDS = 10

WEBAPP_URL = config("WEBAPP_URL", default="http://host.docker.internal:8000")


def _get_json(path: str):
    """GET JSON from the webapp API, or raise a clear error if unreachable"""
    url = f"{WEBAPP_URL}{path}"
    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(
            f"Webapp API unreachable at {url}: check that the webapp is"
            " running (locally: `cd webapp && make runserver`) and that"
            " the WEBAPP_URL env var points to it"
        ) from e
    return response.json()


@functools.lru_cache(maxsize=1)
def get_sources_from_webapp() -> list[dict]:
    """Get the list of sources from the webapp API"""
    return _get_json("/api/qfdmo/sources")


@functools.lru_cache(maxsize=1)
def get_acteur_types_from_webapp() -> list[dict]:
    """Get the list of acteur types from the webapp API"""
    return _get_json("/api/qfdmo/acteurs/types")


@functools.lru_cache(maxsize=1)
def get_acteur_columns_from_webapp() -> dict:
    """Get the list of acteur columns from the webapp API:
    {
        "vue_acteur": {"with_properties": [...], "db_only": [...]},
        "revision_acteur": {"with_properties": [...], "db_only": [...]},
    }
    """
    return _get_json("/api/qfdmo/acteurs/columns")
