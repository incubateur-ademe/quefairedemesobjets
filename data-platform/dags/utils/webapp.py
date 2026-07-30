"""Utilities to fetch webapp data through its HTTP API.

Used at DAG parse time instead of the Django ORM so the DAG processor
doesn't pay the cost of django.setup() + DB connections on every parse
(which caused DagBag import timeouts, see
https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#top-level-python-code)
"""

import functools
import os

import requests

WEBAPP_URL_DEFAULT = "http://host.docker.internal:8000"
TIMEOUT_SECONDS = 10


def webapp_url() -> str:
    """Base URL of the webapp, configurable via the WEBAPP_URL env var"""
    return os.environ.get("WEBAPP_URL", WEBAPP_URL_DEFAULT).rstrip("/")


@functools.lru_cache(maxsize=1)
def acteurs_metadata() -> dict:
    """Referentials (sources, acteur types) and acteurs model fields
    from the webapp API, see /api/qfdmo/metadata/acteurs:
    {
        "sources": {code: id, ...},
        "acteur_types": {code: id, ...},
        "model_fields": {
            "vue_acteur": {"with_properties": [...], "db_only": [...]},
            "revision_acteur": {"with_properties": [...], "db_only": [...]},
        },
    }
    """
    url = f"{webapp_url()}/api/qfdmo/metadata/acteurs"
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
