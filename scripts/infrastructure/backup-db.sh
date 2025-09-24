#!/bin/bash
# TODO: lire l'environnement local directement pour le nom de la db

# Récupérer l'ID de l'instance
INSTANCE_ID=$(scw rdb instance list | grep "lvao-prod-webapp" | awk '{print $1}')
TODAY=$(date +%Y%m%d)
EXISTING_BACKUPS=$(scw rdb backup list instance-id=$INSTANCE_ID | grep "$TODAY")

if [ -z "$INSTANCE_ID" ]; then
    echo "Instance lvao-prod-webapp non trouvée"
    exit 1
fi

if [ -n "$EXISTING_BACKUPS" ]; then
    echo "Un backup a déjà été effectué aujourd'hui :"
    echo "$EXISTING_BACKUPS"
    read -p "Voulez-vous continuer et créer un nouveau backup ? (o/n): " CONTINUE
    if [[ "$CONTINUE" != "o" && "$CONTINUE" != "O" ]]; then
        echo "Création de backup annulée. Utilisation du dernier backup existant"
        # TODO: display $BACKUP_ID here and download it instead of
        # exiting.
        exit 0
    fi
fi

# Créer le backup
BACKUP_NAME="backup-manuel-qfdmo-$(date +%Y%m%d%H%M%S)"
# Définir la date d'expiration dans une semaine au format ISO 8601
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    EXPIRATION_DATE=$(date -u -v+7d +"%Y-%m-%dT%H:%M:%SZ")
else
    # Linux
    EXPIRATION_DATE=$(date -u --date="7 days" +"%Y-%m-%dT%H:%M:%SZ")
fi
echo "Création du backup $BACKUP_NAME (expire le $EXPIRATION_DATE)..."
BACKUP_ID=$(scw rdb backup create instance-id=$INSTANCE_ID database-name=webapp name=$BACKUP_NAME expires-at=$EXPIRATION_DATE | grep "^ID\s" | awk '{print $2}')

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

rm -rf *.custom

scw rdb backup download $BACKUP_ID
cd ..

echo "Backup terminé et téléchargé avec succès !"
