#! /bin/bash

echo "Syncing dags from s3 to ./dags"

AWS_SECRET_ACCESS_KEY=$CELLAR_ADDON_KEY_SECRET AWS_ACCESS_KEY_ID=$CELLAR_ADDON_KEY_ID\
 aws --endpoint-url https://$CELLAR_ADDON_HOST s3 sync --delete --exclude .env.template --exclude .env\
  --exclude download_dags.py s3://prod-qfdmo-airflow-dags $AIRFLOW__CORE__DAGS_FOLDER

exit 0
