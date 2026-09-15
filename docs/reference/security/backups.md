# Sauvegardes

Stratégies de sauvegarde des données applicatives, des bases et de l'état d'infrastructure.

> **Voir aussi** : [Plan de continuité d'activité (PCA)](pca.md), [Plan de reprise d'activité (PRA)](pra.md), [Provisioning](../infrastructure/provisioning.md), [Architecture des bases](../db/db_organisation.md).

## Backups automatiques

| Élément                                    | Stratégie                                                                                         |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| DB Webapp / Warehouse / Airflow (Scaleway) | Backups natifs RDB — rétention point-in-time 24 h + dumps quotidiens 7 j, **copie cross-region**. |
| Bucket `qfdmo-interface`                   | Versioning S3 Scaleway.                                                                           |
| Bucket `lvao-opendata`                     | Snapshots horodatés compilés par le DAG `export_opendata_dag` en plus du `acteurs.csv` courant.   |
| État Terraform                             | Bucket `lvao-terraform-state` (versionné, chiffré).                                               |

## Synchronisation prod → preprod

| Élément           | Stratégie                                                 |
| ----------------- | --------------------------------------------------------- |
| Sync hebdomadaire | Hebdo dimanche minuit via `sync_databases.yml` (DB + S3). |

Voir [CI/CD — Database synchronization](../infrastructure/ci-cd.md#database-synchronization) pour le détail du workflow.

## Export GitHub Actions

Le workflow [`backup-databases.yml`](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/.github/workflows/backup-databases.yml) génère (ou réutilise) un backup Scaleway RDB des bases `webapp`, `warehouse`, `metabase` et `airflow`, télécharge les dumps `.custom` et les publie en artefacts GitHub (rétention 7 jours).

Déclenchement : **Actions → Backup databases → Run workflow** (choix de l’environnement `prod` / `preprod`).

## Backups manuels

Pour générer un dump à la demande (webapp par défaut) :

```sh
scripts/infrastructure/backup-db.sh
```

Pour les quatre bases :

```sh
scripts/infrastructure/backup-db.sh --quiet --env prod --database all
```
