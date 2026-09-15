#!/bin/bash
set -euo pipefail

# Create and download Scaleway RDB backups as pg_dump custom (.custom) files.
#
# Databases:
#   webapp     → instance lvao-{env}-webapp,     database webapp
#   warehouse  → instance lvao-{env}-warehouse,  database warehouse
#   metabase   → instance lvao-{env}-warehouse,  database metabase
#   airflow    → instance lvao-{env}-warehouse,  database airflow

QUIET=false
ENV="prod"
LATEST=false
OUTPUT_DIR=""
DATABASES=("webapp")

usage() {
    echo "Usage: $0 [--quiet|-q] [--env|-e ENV] [--database|-d NAME] [--output-dir|-o DIR] [--latest|-l] [--help|-h]"
    echo "  --quiet, -q:              Do not prompt for confirmation"
    echo "  --env, -e ENV:            Environment (default: prod)"
    echo "  --database, -d NAME:      Database to backup: webapp, warehouse, metabase, airflow, or all"
    echo "                            Comma-separated list accepted. Default: webapp"
    echo "  --output-dir, -o DIR:     Directory to write .custom files (default: tmpbackup-{ENV})"
    echo "  --latest, -l:             Reuse the latest ready backup instead of creating one"
    echo "  --help, -h:               Show this help"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --quiet|-q)
            QUIET=true
            shift
            ;;
        --env|-e)
            ENV="$2"
            shift 2
            ;;
        --latest|-l)
            LATEST=true
            shift
            ;;
        --database|-d)
            if [ "$2" = "all" ]; then
                DATABASES=("webapp" "warehouse" "metabase" "airflow")
            else
                IFS=',' read -ra DATABASES <<< "$2"
            fi
            shift 2
            ;;
        --output-dir|-o)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

command -v scw >/dev/null || { echo "scw CLI is required" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq is required" >&2; exit 1; }

OUTPUT_DIR="${OUTPUT_DIR:-tmpbackup-${ENV}}"
mkdir -p "$OUTPUT_DIR"

json_array() {
    jq -c --arg wrap "$1" 'if type == "array" then . else (.[$wrap] // .) end'
}

instance_name_for() {
    case "$1" in
        webapp)
            echo "lvao-${ENV}-webapp"
            ;;
        warehouse|metabase|airflow)
            echo "lvao-${ENV}-warehouse"
            ;;
        *)
            echo "Unknown database '$1'. Expected: webapp, warehouse, metabase, airflow." >&2
            return 1
            ;;
    esac
}

get_instance_id() {
    local instance_name="$1"
    local instance_id
    instance_id=$(
        scw rdb instance list name="$instance_name" -o json \
            | json_array instances \
            | jq -r --arg n "$instance_name" '[.[] | select(.name == $n) | .id] | first // empty'
    )
    if [ -z "$instance_id" ]; then
        echo "Instance ${instance_name} not found" >&2
        return 1
    fi
    echo "$instance_id"
}

expiration_date() {
    if date -v+7d > /dev/null 2>&1; then
        date -u -v+7d +"%Y-%m-%dT%H:%M:%SZ"
    else
        date -u -d "+7 days" +"%Y-%m-%dT%H:%M:%SZ"
    fi
}

wait_backup_ready() {
    local backup_id="$1"
    echo "Waiting for backup ${backup_id} to become ready..."
    scw rdb backup wait "$backup_id" timeout=90m
}

download_backup() {
    local backup_id="$1"
    local dest="$2"
    echo "Downloading backup ${backup_id} to ${dest}..."
    scw rdb backup download "$backup_id" output="$dest"
    echo "Downloaded $(du -h "$dest" | awk '{print $1}') → ${dest}"
}

backup_database() {
    local db_name="$1"
    local instance_name instance_id backup_id dest today

    instance_name=$(instance_name_for "$db_name")
    instance_id=$(get_instance_id "$instance_name")
    dest="${OUTPUT_DIR}/${db_name}.custom"
    today=$(date -u +%Y-%m-%d)

    echo "==> Backing up ${db_name} on ${instance_name} (${instance_id})"

    if [ "$LATEST" = true ]; then
        backup_id=$(
            scw rdb backup list instance-id="$instance_id" order-by=created_at_desc -o json \
                | json_array database_backups \
                | jq -r --arg db "$db_name" '
                    [.[] | select(.status == "ready" and .database_name == $db) | .id]
                    | first // empty
                '
        )
        if [ -z "$backup_id" ]; then
            echo "No ready backup found for ${db_name} on ${instance_name}" >&2
            return 1
        fi
        echo "Reusing backup ${backup_id}"
        download_backup "$backup_id" "$dest"
        return 0
    fi

    if [ "$QUIET" = false ]; then
        local existing
        existing=$(
            scw rdb backup list instance-id="$instance_id" -o json \
                | json_array database_backups \
                | jq -r --arg db "$db_name" --arg today "$today" '
                    .[]
                    | select(.database_name == $db and (.created_at | startswith($today)))
                    | "\(.id)\t\(.name)\t\(.status)\t\(.created_at)"
                ' || true
        )
        if [ -n "$existing" ]; then
            echo "A backup of ${db_name} already exists today:"
            echo "$existing"
            read -r -p "Create a new backup anyway? (o/n): " CONTINUE
            if [[ "$CONTINUE" != "o" && "$CONTINUE" != "O" ]]; then
                echo "Skipping creation of a new backup for ${db_name}"
                return 0
            fi
        fi
    fi

    local backup_name expires_at
    backup_name="backup-manuel-qfdmo-${db_name}-$(date +%Y%m%d%H%M%S)"
    expires_at=$(expiration_date)
    echo "Creating backup ${backup_name} (expires ${expires_at})..."
    backup_id=$(
        scw rdb backup create \
            instance-id="$instance_id" \
            database-name="$db_name" \
            name="$backup_name" \
            expires-at="$expires_at" \
            -o json \
            | jq -r '.id'
    )
    if [ -z "$backup_id" ] || [ "$backup_id" = "null" ]; then
        echo "Failed to create backup for ${db_name}" >&2
        return 1
    fi

    wait_backup_ready "$backup_id"
    download_backup "$backup_id" "$dest"
}

for db in "${DATABASES[@]}"; do
    db="${db// /}"
    [ -n "$db" ] || continue
    backup_database "$db"
done

echo "Backup finished. Files in ${OUTPUT_DIR}:"
ls -lh "${OUTPUT_DIR}"/*.custom
