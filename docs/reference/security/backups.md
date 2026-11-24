# Sauvegardes

Stratégies de sauvegarde des données applicatives, des bases et de l'état d'infrastructure.

> **Voir aussi** : [Plan de continuité d'activité (PCA)](pca.md), [Plan de reprise d'activité (PRA)](pra.md), [Provisioning](../infrastructure/provisioning.md), [Architecture des bases](../db/db_organisation.md).

## Sauvegarde quotidienne chiffrée

Un Serverless Job Scaleway (`lvao-prod-backup`, stack `infrastructure/environments/prod/backup`) tourne chaque nuit à 2 h et écrit dans le bucket `lvao-prod-backups` :

| Contenu                                                                | Emplacement dans le bucket    | Rétention                             |
| ---------------------------------------------------------------------- | ----------------------------- | ------------------------------------- |
| Dump des bases `webapp`, `airflow` et `metabase`                       | `db/<base>/<AAAA-MM-JJ>.dump` | 30 jours                              |
| Copie de `qfdmo-interface`, `lvao-data-source`, `lvao-terraform-state` | `buckets/<bucket>/`           | Miroir, versions précédentes 30 jours |

La base `warehouse` n'est pas sauvegardée par ce job : elle est reconstruite par dbt à partir de la base `webapp` et des sources.

Le script du job est `infrastructure/modules/backup/backup.sh`. Il crée les dumps avec `scw rdb backup` (aucun mot de passe de base n'est nécessaire) et les copie avec `rclone`.

### Chiffrement

Chaque fichier est chiffré par `rclone crypt` avant de quitter le job : le bucket ne contient que du chiffré, et peut être déplacé chez un autre fournisseur en changeant la destination du job. Le chiffrement côté serveur de Scaleway (SSE-ONE) est aussi activé sur le bucket.

⚠️ Sans le mot de passe de chiffrement, les sauvegardes sont illisibles. Il est généré par la stack et doit être copié dans le gestionnaire de mots de passe de l'équipe :

```sh
cd infrastructure/environments/prod/backup
terragrunt output -raw encryption_password
```

### Restaurer

Avec `rclone` et le mot de passe de chiffrement :

```sh
export RCLONE_CONFIG_S3_TYPE=s3 RCLONE_CONFIG_S3_PROVIDER=Scaleway
export RCLONE_CONFIG_S3_REGION=fr-par RCLONE_CONFIG_S3_ENDPOINT=s3.fr-par.scw.cloud
export RCLONE_CONFIG_S3_ACCESS_KEY_ID=$SCW_ACCESS_KEY RCLONE_CONFIG_S3_SECRET_ACCESS_KEY=$SCW_SECRET_KEY
export RCLONE_CONFIG_BACKUP_TYPE=crypt RCLONE_CONFIG_BACKUP_REMOTE=s3:lvao-prod-backups
export RCLONE_CONFIG_BACKUP_FILENAME_ENCRYPTION=off RCLONE_CONFIG_BACKUP_DIRECTORY_NAME_ENCRYPTION=false
export RCLONE_CONFIG_BACKUP_PASSWORD=$(rclone obscure "<mot de passe de chiffrement>")

# Une base
rclone lsf backup:db/webapp
rclone copy backup:db/webapp/<AAAA-MM-JJ>.dump .
pg_restore -d "$DATABASE_URL" --clean --if-exists --no-acl --no-owner <AAAA-MM-JJ>.dump

# Un bucket
rclone sync backup:buckets/qfdmo-interface s3:qfdmo-interface
```

### Lancer une sauvegarde à la main

```sh
scw jobs definition list name=lvao-prod-backup
scw jobs definition start <id>
```

## Sauvegardes natives Scaleway

| Élément                               | Stratégie                                                                                                     |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Instances RDB `webapp` et `warehouse` | Snapshot quotidien du volume, conservé 30 jours (`webapp`) ou 7 jours (`warehouse`), dans la région `fr-par`. |
| Buckets critiques                     | Versioning activé sur `qfdmo-interface`, `lvao-data-source` et `lvao-terraform-state`.                        |
| Bucket `lvao-opendata`                | Non versionné : réécrit à chaque exécution du DAG `export_opendata_dag`.                                      |

Les snapshots restaurent une instance entière chez Scaleway. Ils ne sont pas exportables : la sauvegarde quotidienne ci-dessus est la seule copie exploitable hors de l'instance.

## Synchronisation prod → preprod

| Élément           | Stratégie                                                 |
| ----------------- | --------------------------------------------------------- |
| Sync hebdomadaire | Hebdo dimanche minuit via `sync_databases.yml` (DB + S3). |

Voir [CI/CD — Database synchronization](../infrastructure/ci-cd.md#database-synchronization) pour le détail du workflow.

## Dump manuel

Pour générer un dump de la base `webapp` à la demande :

```sh
scripts/infrastructure/backup-db.sh
```
