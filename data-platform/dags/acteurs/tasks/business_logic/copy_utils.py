import logging
import subprocess
import tempfile
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

    # Create the dump
    with tempfile.NamedTemporaryFile(suffix=".dump") as tmp_dump_file:
        dump_file = tmp_dump_file.name

        with open(dump_file, "wb") as f:
            subprocess.run(
                dump_cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                check=True,
            )

        logger.info("✅ Dump créé")

        # Restore the dump
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
            dump_file,
        ]

        result = subprocess.run(restore_cmd, capture_output=True)
        if result.returncode != 0:
            logger.warning(
                f"⚠️  pg_restore exited with code {result.returncode}:\n"
                f"{result.stderr.decode()}"
            )
