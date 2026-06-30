#!/bin/bash
# Usage: sh scripts/db_restore.sh <db_label> [dump_dir]
#
# Restore a PostgreSQL custom-format dump into a Docker database container.
#
#   db_label   - one of: prod, preprod, sample
#   dump_dir   - directory containing .custom dump files (default: tmpbackup-<db_label>)
#
# Runs psql and pg_restore inside the matching Docker PostgreSQL container
# to avoid version mismatches between host and remote pg_dump versions.

set -euo pipefail

DB_LABEL="${1:-}"
DUMP_DIR="${2:-tmpbackup-${DB_LABEL}}"

if [ -z "$DB_LABEL" ]; then
    echo "Usage: sh scripts/db_restore.sh <db_label> [dump_dir]" >&2
    echo "  db_label: prod | preprod | sample" >&2
    exit 1
fi

# Determine which Docker service and database URL to use
case "$DB_LABEL" in
    prod|preprod|sample)
        DOCKER_SERVICE="lvao-webapp-db"
        DB_USER="webapp"
        DB_NAME="webapp"
        ;;
    *)
        echo "Unknown db_label: $DB_LABEL (use: prod, preprod, sample)" >&2
        exit 1
        ;;
esac

# Find the dump file
DUMP_FILE=$(find "$DUMP_DIR" -type f -name "*.custom" -print -quit 2>/dev/null || true)

if [ -z "$DUMP_FILE" ]; then
    echo "No .custom dump file found in $DUMP_DIR" >&2
    exit 1
fi

echo "Restoring $DUMP_FILE into docker:$DOCKER_SERVICE ($DB_NAME)…"

# 1. Create extensions inside the container (pg_restore doesn't restore these)
echo "  Creating extensions…"
docker compose exec -T "$DOCKER_SERVICE" psql -U "$DB_USER" -d "$DB_NAME" -f /dev/stdin < scripts/sql/create_extensions.sql

# 2. Restore the dump inside the container (same psql/pg_restore version as the DB)
echo "  Restoring dump…"
docker compose exec -T "$DOCKER_SERVICE" pg_restore -v -d "$DB_NAME" -U "$DB_USER" \
    --schema=public --clean --no-acl --no-owner --no-privileges < "$DUMP_FILE"

echo "✅ Restore complete: $DB_LABEL"
