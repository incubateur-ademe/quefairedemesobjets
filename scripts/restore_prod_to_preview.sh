#!/usr/bin/env bash
#
# Restore the prod webapp database into the preview webapp database.
#
# Source of truth for credentials: Scaleway Secret Manager. Per-environment
# isolation comes from the Scaleway project_id, so secret names are identical
# across envs (`DATABASE_URL`, `DATABASE_URL_RO`).
#
# Required secrets:
#   - in the PROD project   : DATABASE_URL_RO  (read-only conn string to prod)
#   - in the PREVIEW project: DATABASE_URL     (admin conn string to preview)
#
# Required tools on the operator machine: scw, pg_dump, pg_restore, psql.
# All three pg tools must match the server's PostgreSQL major version (16).
#
# Required environment variables (Scaleway project IDs):
#   SCW_PROD_PROJECT_ID    — project that holds prod resources
#   SCW_PREVIEW_PROJECT_ID — project that holds preview resources
#
# Usage:
#   SCW_PROD_PROJECT_ID=… SCW_PREVIEW_PROJECT_ID=… \
#     ./scripts/restore_prod_to_preview.sh

set -euo pipefail

PROD_DATABASE_URL_SECRET="${PROD_DATABASE_URL_SECRET:-DATABASE_URL_RO}"
PREVIEW_DATABASE_URL_SECRET="${PREVIEW_DATABASE_URL_SECRET:-DATABASE_URL}"
DUMP_FILE="${DUMP_FILE:-/tmp/lvao-prod-webapp.dump}"
SQL_EXTENSIONS_PATH="$(dirname "$0")/sql/create_extensions.sql"

: "${SCW_PROD_PROJECT_ID:?must be set to the Scaleway project_id of the prod project}"
: "${SCW_PREVIEW_PROJECT_ID:?must be set to the Scaleway project_id of the preview project}"

cleanup() {
  rm -f "${DUMP_FILE}"
}
trap cleanup EXIT

# Reads the latest enabled version of a secret from Scaleway Secret Manager
# in the specified project. Scaleway returns the data already base64-decoded
# in the `data` field when -o json is used with `secret access-by-name`.
read_secret() {
  local project_id="$1"
  local secret_name="$2"
  scw secret secret access-by-name \
    name="${secret_name}" \
    project-id="${project_id}" \
    revision=latest_enabled \
    -o json \
    | python3 -c 'import json,sys,base64; d=json.load(sys.stdin); print(base64.b64decode(d["data"]).decode())'
}

echo "→ Reading source connection string from prod project…"
PROD_DATABASE_URL="$(read_secret "${SCW_PROD_PROJECT_ID}" "${PROD_DATABASE_URL_SECRET}")"

echo "→ Reading target connection string from preview project…"
PREVIEW_DATABASE_URL="$(read_secret "${SCW_PREVIEW_PROJECT_ID}" "${PREVIEW_DATABASE_URL_SECRET}")"

echo "→ Dumping prod webapp database to ${DUMP_FILE}…"
pg_dump \
  --format=custom \
  --no-owner --no-acl --no-privileges \
  --schema=public \
  --file="${DUMP_FILE}" \
  "${PROD_DATABASE_URL}"

echo "→ Dropping all tables in preview webapp public schema…"
# -tA: tuples-only, unaligned; one bare table name per line. NUL-delimited
# read avoids word-splitting on names that contain whitespace or quotes.
psql "${PREVIEW_DATABASE_URL}" -tAc \
  "SELECT tablename FROM pg_tables WHERE schemaname='public'" \
  | while IFS= read -r table; do
      [ -z "${table}" ] && continue
      psql "${PREVIEW_DATABASE_URL}" -c "DROP TABLE IF EXISTS \"${table}\" CASCADE;" >/dev/null
    done

echo "→ Creating PostgreSQL extensions on preview…"
psql -d "${PREVIEW_DATABASE_URL}" -f "${SQL_EXTENSIONS_PATH}" >/dev/null

echo "→ Restoring dump into preview…"
pg_restore \
  --schema=public \
  --no-owner --no-acl --no-privileges \
  --dbname "${PREVIEW_DATABASE_URL}" \
  "${DUMP_FILE}"

echo "✓ Done. You may now run Django migrations against preview:"
echo "    DATABASE_URL=\"${PREVIEW_DATABASE_URL}\" uv run python webapp/manage.py migrate"
