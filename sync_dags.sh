#! /bin/bash

echo "Syncing dags from s3 to ./dags"
echo "with env variable :"
# afficher la longuer de la variable $CELLAR_ADDON_KEY_ID et les 3 dernières lettres
echo "CELLAR_ADDON_KEY_ID: ${#CELLAR_ADDON_KEY_ID} ${CELLAR_ADDON_KEY_ID: -3}"
echo "CELLAR_ADDON_KEY_SECRET: ${#CELLAR_ADDON_KEY_SECRET} ${CELLAR_ADDON_KEY_SECRET: -3}"
echo "CELLAR_ADDON_HOST: $CELLAR_ADDON_HOST"
echo "CELLAR_ADDON_BUCKET: $CELLAR_ADDON_BUCKET"

export AWS_SECRET_ACCESS_KEY=$CELLAR_ADDON_KEY_SECRET
export AWS_ACCESS_KEY_ID=$CELLAR_ADDON_KEY_ID

echo "aws --endpoint-url https://$CELLAR_ADDON_HOST s3 sync --delete --exclude .env.template --exclude .env --exclude download_dags.py s3://$CELLAR_ADDON_BUCKET $AIRFLOW__CORE__DAGS_FOLDER"
aws --endpoint-url https://$CELLAR_ADDON_HOST s3 sync --delete --exclude .env.template --exclude .env --exclude download_dags.py s3://$CELLAR_ADDON_BUCKET $AIRFLOW__CORE__DAGS_FOLDER

exit 0
