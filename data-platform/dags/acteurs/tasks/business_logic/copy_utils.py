import logging
import subprocess
from typing import Optional

import psycopg2

logger = logging.getLogger(__name__)


def drop_tables(dsn: str, tables: list[str]) -> None:
    """Drop tables in the destination DB before restoring."""
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    with conn.cursor() as cursor:
        for table in tables:
            cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
            logger.info(f"  ✓ Table {table} supprimée")
    conn.close()


def dump_and_restore_db(
    source_dsn: str,
    dest_dsn: str,
    tables: Optional[list[str]] = None,
    schema_only: bool = False,
    data_only: bool = False,
) -> None:
    # Build the pg_dump command
    dump_cmd = [
        "pg_dump",
        "-d",
        source_dsn,
        "--schema=public",
        "--no-owner",
        "--no-acl",
        "--format=custom",
    ]

    if schema_only:
        dump_cmd.append("--schema-only")
    elif data_only:
        dump_cmd.append("--data-only")

    # Add specific tables if provided
    if tables:
        for table in tables:
            dump_cmd.append("--table")
            dump_cmd.append(f"public.{table}")

    logger.info("📦 Démarrage du dump/restore en pipeline...")

    # Pipe pg_dump directly into pg_restore — no intermediate file on disk.
    # For a 3GB database this avoids ~6GB of sequential disk I/O per call.
    dump_proc = subprocess.Popen(
        dump_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    restore_cmd = [
        "pg_restore",
        "-d",
        dest_dsn,
        "--schema=public",
        "--no-owner",
        "--no-acl",
        "--no-privileges",
        "--clean",
        "--if-exists",
        "--disable-triggers",
    ]

    restore_proc = subprocess.Popen(
        restore_cmd,
        stdin=dump_proc.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Close the pipe in the parent so the pipeline doesn't deadlock
    dump_proc.stdout.close()

    dump_stderr = dump_proc.stderr.read()
    restore_stdout, restore_stderr = restore_proc.communicate()

    dump_retcode = dump_proc.wait()

    if dump_retcode != 0:
        logger.warning(
            f"⚠️  pg_dump exited with code {dump_retcode}:\n"
            f"{dump_stderr.decode(errors='replace')}"
        )
    if restore_proc.returncode != 0:
        logger.warning(
            f"⚠️  pg_restore exited with code {restore_proc.returncode}:\n"
            f"{restore_stderr.decode(errors='replace')}"
        )

    logger.info("✅ Pipeline dump/restore terminé")
