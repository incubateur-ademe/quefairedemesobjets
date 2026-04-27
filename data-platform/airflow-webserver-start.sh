#!/bin/bash
set -e

echo "Running database migrations..."
airflow db migrate

echo "Creating admin user..."
airflow users create \
  --role Admin \
  --username ${_AIRFLOW_WWW_USER_USERNAME:-airflow} \
  --password ${_AIRFLOW_WWW_USER_PASSWORD:-airflow} \
  --email ${_AIRFLOW_WWW_USER_EMAIL:-admin@example.com} \
  --firstname Admin \
  --lastname Admin || true

echo "Starting API server..."
exec airflow api-server
