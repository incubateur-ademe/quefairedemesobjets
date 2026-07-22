"""A DB Cleanup DAG
- Originally developped by Astronomer: https://www.astronomer.io/docs/learn/cleanup-dag-tutorial
- Modified to fit our needs"""

import shlex
from datetime import UTC, datetime, timedelta

from airflow.cli.commands.db_command import all_tables
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import Param, dag
from airflow.sdk.bases.operator import chain
from shared.config.schedules import SCHEDULES
from shared.config.start_dates import START_DATES
from shared.config.tags import TAGS

DAYS_TO_KEEP = 15
DEFAULT_BATCH_SIZE = 1000
DB_CLEANUP_SCRIPT = "/opt/airflow/scripts/db_cleanup.sh"


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
            False,
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
        "batch_size": Param(
            default=DEFAULT_BATCH_SIZE,
            type="integer",
            description_md="""**📦 Taille du batch (lignes par transaction)**:
            valeur basse = locks plus courts mais plus de transactions""",
        ),
    },
)
def airflow_cleanup_db():
    def db_cleanup_command(params: dict) -> str:
        cmd = [
            DB_CLEANUP_SCRIPT,
            "db",
            "clean",
            "--clean-before-timestamp",
            params["clean_before_timestamp"],
            "--batch-size",
            str(params["batch_size"]),
            "--skip-archive",
            "--verbose",
            "--yes",
        ]
        if params["dry_run"]:
            cmd.append("--dry-run")
        if params["tables"]:
            cmd.extend(["--tables", ",".join(params["tables"])])
        return " ".join(shlex.quote(arg) for arg in cmd)

    def db_archive_cleanup_command(params: dict) -> str:
        cmd = [
            DB_CLEANUP_SCRIPT,
            "db",
            "drop-archived",
            "--yes",
        ]
        if params["tables"]:
            cmd.extend(["--tables", ",".join(params["tables"])])
        return " ".join(shlex.quote(arg) for arg in cmd)

    # Trailing space prevents Airflow from interpreting the command as a
    # path to a Jinja template file (BashOperator.template_ext = ('.sh',)).
    db_cleanup_bash_command = "{{ db_cleanup_command(params) }} "
    db_archive_cleanup_bash_command = "{{ db_archive_cleanup_command(params) }} "

    db_cleanup = BashOperator(
        task_id="db_cleanup",
        bash_command=db_cleanup_bash_command,
        do_xcom_push=False,
    )

    # Defensive cleanup of any archive tables left behind by older runs
    # (before --skip-archive was used) or by partial failures.
    db_archive_cleanup = BashOperator(
        task_id="clean_archive_tables",
        bash_command=db_archive_cleanup_bash_command,
        do_xcom_push=False,
        trigger_rule="all_done",
    )

    db_cleanup.dag.user_defined_macros = {
        **(db_cleanup.dag.user_defined_macros or {}),
        "db_cleanup_command": db_cleanup_command,
        "db_archive_cleanup_command": db_archive_cleanup_command,
    }

    chain(db_cleanup, db_archive_cleanup)


airflow_cleanup_db()
