import logging

from acteurs.tasks.business_logic.copy_db_schema import copy_db_schema
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)


def copy_db_schema_task():
    return PythonOperator(
        task_id="copy_db_schema",
        python_callable=copy_db_schema_wrapper,
    )


def _resolve_source_dsn(params: dict) -> str | None:
    from django.conf import settings

    source_db = params.get("source_db", "current_env")
    if source_db == "prod":
        prod_url = settings.PROD_DATABASE_URL
        if not prod_url:
            raise ValueError("PROD_DATABASE_URL must be set to use source_db='prod'")
        return prod_url
    return None


def copy_db_schema_wrapper(ti, params):
    copy_db_schema(source_dsn=_resolve_source_dsn(params))
