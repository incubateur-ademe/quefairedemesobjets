"""A DB Cleanup DAG
- Originally developped by Astronomer: https://www.astronomer.io/docs/learn/cleanup-dag-tutorial
- Modified to fit our needs"""

import logging
from datetime import UTC, datetime, timedelta
from typing import List, Optional

from airflow.cli.commands.db_command import all_tables
from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.operators.bash import BashOperator
from airflow.utils.db import reflect_tables
from airflow.utils.db_cleanup import _effective_table_names
from airflow.utils.session import NEW_SESSION, provide_session
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS
from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

DAYS_TO_KEEP = 7


@dag(
    dag_id="airflow_cleanup_db",
    dag_display_name="Maintenance - Airflow - Nettoyer la DB (XCOM, logs, etc.)",
    schedule=SCHEDULES.EVERY_DAY_AT_00_00,
    start_date=START_DATES.DEFAULT,
    is_paused_upon_creation=False,
    render_template_as_native_obj=True,
    max_active_tasks=1,
    tags=[
        TAGS.AIRFLOW,
        TAGS.MAINTENANCE,
        TAGS.NETTOYAGE,
        TAGS.XCOM,
        TAGS.CLEANUP,
        TAGS.DB,
        TAGS.LOGS,
    ],
    params={
        "dry_run": Param(
            # DAG is meant to run continuously hence the default is False
            default=False,
            type="boolean",
            description="🚱 Si coché: on affiche de l'info mais pas de nettoyage",
        ),
        "clean_before_timestamp": Param(
            default=str(datetime.now(tz=UTC) - timedelta(days=DAYS_TO_KEEP)),
            type="string",
            format="date-time",
            description_md=f"""**📅 Date au delà de laquelle on supprime**: par défaut
            = aujourd'hui - {DAYS_TO_KEEP} jours""",
        ),
        "tables": Param(
            default=[],
            type=["null", "array"],
            examples=all_tables,
            description_md="**📅 Tables à nettoyer**: par défaut = toutes",
        ),
        "batch_size_days": Param(
            default=7,
            type="integer",
            description_md="""**📦 Taille du batch**: par défaut on supprime
            {batch_size_days} jours à la fois""",
        ),
    },
)
def airflow_cleanup_db():

    @provide_session
    def get_oldest_timestamp(
        tables,
        session: Session = NEW_SESSION,
    ) -> Optional[str]:
        oldest_timestamp_list = []
        existing_tables = reflect_tables(tables=None, session=session).tables
        _, effective_config_dict = _effective_table_names(table_names=tables)
        for table_name, table_config in effective_config_dict.items():
            if table_name in existing_tables:  # type: ignore
                orm_model = table_config.orm_model
                recency_column = table_config.recency_column
                oldest_execution_date = (
                    session.query(func.min(recency_column))  # type: ignore
                    .select_from(orm_model)
                    .scalar()
                )
                if oldest_execution_date:
                    oldest_timestamp_list.append(oldest_execution_date.isoformat())
                else:
                    logger.info(f"No data found for {table_name}, skipping...")
            else:
                logger.warning(f"Table {table_name} not found. Skipping.")

        if oldest_timestamp_list:
            return min(oldest_timestamp_list)

    @task
    def get_chunked_timestamps(**context) -> List:
        batches = []
        start_chunk_time = get_oldest_timestamp(context["params"]["tables"])
        if start_chunk_time:
            start_ts = datetime.fromisoformat(start_chunk_time)
            end_ts = datetime.fromisoformat(context["params"]["clean_before_timestamp"])
            batch_size_days = context["params"]["batch_size_days"]

            while start_ts < end_ts:
                batch_end = min(start_ts + timedelta(days=batch_size_days), end_ts)
                batches.append({"BATCH_TS": batch_end.isoformat()})
                start_ts += timedelta(days=batch_size_days)
        logger.info("Number of batches: %s", len(batches))
        return batches

    # The "clean_archive_tables" task drops archived tables created by
    # the previous "clean_db" task, in case that task fails due to an error or timeout.
    db_archive_cleanup = BashOperator(
        task_id="clean_archive_tables",
        bash_command="""\
            airflow db drop-archived \
        {% if params.tables -%}
             --tables {{ params.tables|join(',') }} \
        {% endif -%}
             --yes \
        """,
        do_xcom_push=False,
        trigger_rule="all_done",
    )

    chunked_timestamps = get_chunked_timestamps()

    # dry_run mode is directly integrated using the --dry-run flag
    _ = (  # noqa: F841
        BashOperator.partial(
            task_id="db_cleanup",
            bash_command="""\
            airflow db clean \
             --clean-before-timestamp $BATCH_TS \
        {% if params.dry_run -%}
             --dry-run \
        {% endif -%}
             --skip-archive \
        {% if params.tables -%}
             --tables '{{ params.tables|join(',') }}' \
        {% endif -%}
             --verbose \
             --yes \
        """,
            append_env=True,
            do_xcom_push=False,
        ).expand(env=chunked_timestamps)
        >> db_archive_cleanup
    )


airflow_cleanup_db()
