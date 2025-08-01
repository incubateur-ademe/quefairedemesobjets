#!/bin/bash

# Vérifier que ENVIRONMENT est définie et valide
if [ "$ENVIRONMENT" != "prod" ] && [ "$ENVIRONMENT" != "preprod" ]; then
    echo "❌ Erreur : ENVIRONMENT doit être 'prod' ou 'preprod'"
    exit 1
fi

# Récupérer l'ID de l'instance
DB_ID=$(scw rdb instance list -o json | jq -r ".[] | select(.name==\"lvao-${ENVIRONMENT}-db\") | .id")

if [ -z "$DB_ID" ]; then
    echo "❌ Erreur : Impossible de trouver l'instance lvao-${ENVIRONMENT}-db"
    exit 1
fi

echo "🔍 Instance ${ENVIRONMENT} trouvée : $DB_ID"

# Purger les logs
echo "🗑️  Purge des logs en cours..."
scw rdb log purge instance-id=$DB_ID

echo "✅ Purge des logs terminée"