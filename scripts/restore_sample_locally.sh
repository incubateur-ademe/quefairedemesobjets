#!/usr/bin/env bash
set -euo pipefail

DUMP_FILE="sample_backup.pgsql"

if [ -z "${REMOTE_SAMPLE_DATABASE_URL:-}" ]; then
    echo "Error: REMOTE_SAMPLE_DATABASE_URL is not set"
    exit 1
fi

if [ -z "${SAMPLE_DATABASE_URL:-}" ]; then
    echo "Error: SAMPLE_DATABASE_URL is not set"
    exit 1
fi

echo "Dumping remote sample database..."
pg_dump --format=custom --no-acl --no-owner --no-privileges "${REMOTE_SAMPLE_DATABASE_URL}" --file="${DUMP_FILE}"

echo "Dropping and recreating public schema..."
psql -d "${SAMPLE_DATABASE_URL}" -c "DROP SCHEMA IF EXISTS public CASCADE;"
psql -d "${SAMPLE_DATABASE_URL}" -c "CREATE SCHEMA IF NOT EXISTS public;"

echo "Creating extensions..."
psql -d "${SAMPLE_DATABASE_URL}" -f scripts/sql/create_extensions.sql

echo "Restoring dump to local sample database..."
pg_restore -d "${SAMPLE_DATABASE_URL}" --schema=public --clean --no-acl --no-owner --no-privileges "${DUMP_FILE}" || true

echo "Removing dump file..."
rm -f "${DUMP_FILE}"

echo "Done."
