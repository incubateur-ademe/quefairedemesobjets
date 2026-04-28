#!/usr/bin/env bash
# Wrapper to run `airflow db ...` admin commands from within an Airflow 3 task.
# Why: the task supervisor (airflow.sdk.execution_time.supervisor) intentionally
# replaces AIRFLOW__DATABASE__SQL_ALCHEMY_CONN with a sentinel in task
# subprocesses to block ORM access from DAGs. We restore it here from the
# AIRFLOW_METADATA_DB_URL mirror set on the worker container.
set -euo pipefail

: "${AIRFLOW_METADATA_DB_URL:?AIRFLOW_METADATA_DB_URL must be set on the worker}"

export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="$AIRFLOW_METADATA_DB_URL"
export AIRFLOW__CORE__SQL_ALCHEMY_CONN="$AIRFLOW_METADATA_DB_URL"

exec airflow "$@"
