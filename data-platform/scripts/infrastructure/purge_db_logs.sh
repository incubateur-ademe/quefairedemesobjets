#!/bin/bash

# Vérifier que ENVIRONMENT est définie et valide
if [ "$ENVIRONMENT" != "prod" ] && [ "$ENVIRONMENT" != "preprod" ]; then
    echo "❌ Erreur : ENVIRONMENT doit être 'prod' ou 'preprod'"
    exit 1
fi

for instance_type in webapp warehouse; do
    INSTANCE=lvao-${ENVIRONMENT}-${instance_type}
    # Récupérer l'ID de l'instance
    DB_ID=$(scw rdb instance list -o json | jq -r ".[] | select(.name==\"${INSTANCE}\") | .id")

    if [ -z "$DB_ID" ]; then
        echo "❌ Erreur : Impossible de trouver l'instance ${INSTANCE}"
        exit 1
    fi

    echo "🔍 Instance ${INSTANCE} trouvée : $DB_ID"

    # Purger les logs
    echo "🗑️  Purge des logs en cours…"
    scw rdb log purge instance-id=$DB_ID

    echo "✅ Purge des logs terminée"
done