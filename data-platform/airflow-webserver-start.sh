#!/bin/bash
set -e

should_migrate="${_AIRFLOW_DB_MIGRATE:-}"
if [[ "${should_migrate}" == "true" || "${should_migrate}" == "1" || "${should_migrate}" == "True" ]]; then
  echo "Running database migrations..."
  airflow db migrate
else
  echo "Skipping database migrations (_AIRFLOW_DB_MIGRATE=${should_migrate})"
fi

should_create_user="${_AIRFLOW_WWW_USER_CREATE:-}"
if [[ "${should_create_user}" == "true" || "${should_create_user}" == "1" || "${should_create_user}" == "True" ]]; then
  echo "Creating admin user..."
  airflow users create \
    --role Admin \
    --username ${_AIRFLOW_WWW_USER_USERNAME:-airflow} \
    --password ${_AIRFLOW_WWW_USER_PASSWORD:-airflow} \
    --email ${_AIRFLOW_WWW_USER_EMAIL:-admin@example.com} \
    --firstname Admin \
    --lastname Admin || true
else
  echo "Skipping admin user creation (_AIRFLOW_WWW_USER_CREATE=${should_create_user})"
fi

echo "Starting API server..."
exec airflow api-server
