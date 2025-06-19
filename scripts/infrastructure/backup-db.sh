#!/bin/bash

# Récupérer l'ID de l'instance
INSTANCE_ID=$(scw rdb instance list | grep "lvao-preprod-db" | awk '{print $1}')

if [ -z "$INSTANCE_ID" ]; then
    echo "Instance lvao-preprod-db non trouvée"
    exit 1
fi

# Créer le backup
BACKUP_NAME="backup-manuel-qfdmo-$(date +%Y%m%d%H%M%S)"
echo "Création du backup $BACKUP_NAME..."
BACKUP_ID=$(scw rdb backup create instance-id=$INSTANCE_ID database-name=qfdmo name=$BACKUP_NAME | grep "^ID\s" | awk '{print $2}')

if [ -z "$BACKUP_ID" ]; then
    echo "Erreur lors de la création du backup"
    exit 1
fi

# Attendre que le backup soit prêt
echo "Attente de la disponibilité du backup..."
while true; do
    STATUS=$(scw rdb backup get $BACKUP_ID | grep "^Status\s" | awk '{print $2}')
    if [ "$STATUS" = "ready" ]; then
        break
    fi
    echo "Status: $STATUS"
    sleep 10
done

# Télécharger le backup
echo "Téléchargement du backup..."

mkdir -p tmpbackup
cd tmpbackup
scw rdb backup download $BACKUP_ID
cd ..

echo "Backup terminé et téléchargé avec succès !"

