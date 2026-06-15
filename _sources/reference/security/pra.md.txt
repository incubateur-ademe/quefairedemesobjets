# Plan de reprise d'activité (PRA)

Procédures de **restauration du service après un sinistre majeur** : perte d'une base de données, corruption de bucket S3, indisponibilité prolongée d'un fournisseur, suppression accidentelle de ressources, compromission.

> **Voir aussi** : [Plan de continuité d'activité (PCA)](pca.md), [Sauvegardes](backups.md), [Revues régulières](reviews.md), [Provisioning](../infrastructure/provisioning.md), [Monitoring](../infrastructure/monitoring.md), [CI/CD](../infrastructure/ci-cd.md).

## Objectifs cibles

> Objectifs internes — non contractualisés avec un tiers à ce jour.

| Périmètre                                | RPO cible (perte de données max.)                | RTO cible (durée d'interruption max.) |
| ---------------------------------------- | ------------------------------------------------ | ------------------------------------- |
| **DB Webapp** (`lvao-prod-webapp`)       | ≤ 1 h (couvert par PITR 24 h)                    | ≤ 4 h                                 |
| **DB Warehouse** (`lvao-prod-warehouse`) | ≤ 24 h (reconstructible par `dbt run`)           | ≤ 8 h                                 |
| **DB Airflow** (`lvao-prod-airflow`)     | ≤ 24 h (métadonnées — perte tolérable)           | ≤ 8 h                                 |
| **Bucket `qfdmo-interface`**             | Versioning S3 (récupération fichier par fichier) | ≤ 2 h                                 |
| **Bucket `lvao-opendata`**               | Dernier snapshot horodaté                        | ≤ 2 h                                 |
| **Webapp Scalingo**                      | Aucune perte (re-deploy depuis `main`)           | ≤ 1 h                                 |
| **Airflow Scaleway**                     | Aucune perte (re-build & push image)             | ≤ 2 h                                 |

## Inventaire des sauvegardes mobilisables

Le détail des stratégies est dans [`backups.md`](backups.md). Synthèse :

| Source                          | Type de sauvegarde                    | Rétention      | Localisation                  |
| ------------------------------- | ------------------------------------- | -------------- | ----------------------------- |
| DB Webapp / Warehouse / Airflow | PITR natif RDB                        | 24 h           | Scaleway `fr-par`             |
| DB Webapp / Warehouse / Airflow | Dumps quotidiens                      | 7 j            | Scaleway `fr-par`             |
| DB Webapp / Warehouse / Airflow | **Copie cross-region**                | 7 j            | Autre région Scaleway         |
| Bucket `qfdmo-interface`        | Versioning S3                         | Indéfini       | Scaleway `fr-par`             |
| Bucket `lvao-opendata`          | Snapshots `YYYYMMDDHHMMSS.csv`        | Indéfini       | Scaleway `fr-par`             |
| État OpenTofu                   | Versioning + chiffrement bucket       | Indéfini       | Bucket `lvao-terraform-state` |
| Code applicatif & IaC           | Git                                   | Indéfini       | GitHub                        |
| Images Docker Airflow           | Container Registry `ns-qfdmo`         | Tags conservés | Scaleway                      |
| Dump manuel à la demande        | `scripts/infrastructure/backup-db.sh` | Selon usage    | Poste opérateur / S3          |

## Scénarios de sinistre & procédures

### Scénario 1 — Corruption / perte de la DB Webapp prod

**Symptômes** : erreurs 500 massives, données absentes, Sentry saturé.

**Procédure**

1. **Geler** les écritures côté webapp si possible (mode maintenance Scalingo).
2. Identifier la fenêtre temporelle saine avec les équipes produit.
3. Depuis la console Scaleway RDB :
   - Restaurer `lvao-prod-webapp` en **PITR** sur le timestamp choisi (≤ 24 h) → instance temporaire `lvao-prod-webapp-restore`.
   - Ou, si la fenêtre dépasse 24 h, restaurer depuis le **dump quotidien le plus récent** (rétention 7 j).
4. Pointer la webapp sur la nouvelle instance :
   - Mettre à jour `DATABASE_URL` dans les variables d'environnement Scalingo.
   - Redémarrer les containers webapp.
5. Vérifier l'application :
   - Healthcheck (`HEALTHCHECK_URLS`).
   - Smoke tests manuels (recherche carte, assistant, Django Admin).
6. Communication Mattermost `lvao-tour-de-controle`.
7. **Post-mortem** : renommer / supprimer l'ancienne instance, mettre à jour Terragrunt (`terraform.tfvars` si endpoint changé), `terragrunt apply --all`.

### Scénario 2 — Perte d'une base secondaire (Warehouse ou Airflow)

| Base             | Stratégie                                                                                                                              |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **DB Warehouse** | Reconstructible intégralement par `dbt run` à partir de la DB Webapp + sources. Restauration PITR optionnelle pour accélérer (≤ 24 h). |
| **DB Airflow**   | Restauration PITR si pertinent. Sinon recréation à vide : Airflow régénère ses métadonnées, les DAGs reprennent au prochain schedule.  |

### Scénario 3 — Suppression / corruption d'un objet S3

| Bucket                 | Procédure                                                                                                                |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `qfdmo-interface`      | Restaurer la version précédente via le **versioning S3** (console Scaleway ou CLI `aws s3api list-object-versions`).     |
| `lvao-opendata`        | Reposter le dernier snapshot horodaté sur `acteurs.csv`, ou relancer le DAG `export_opendata_dag`.                       |
| `lvao-data-source`     | Re-uploader le fichier source d'origine, relancer le DAG `source-s3` concerné.                                           |
| `lvao-{env}-airflow`   | Logs uniquement — perte tolérable, pas d'action requise.                                                                 |
| `lvao-terraform-state` | Restaurer la version précédente du tfstate via versioning. ⚠️ Synchroniser avec un éventuel `terragrunt apply` en cours. |

### Scénario 4 — Indisponibilité prolongée de Scalingo

**Procédure** (basculement d'urgence)

1. Provisionner une plateforme alternative compatible buildpacks (ou un container Docker classique) — l'application est packagée par les buildpacks `apt`, `node`, `python`, `nginx` listés dans `webapp/.buildpacks`.
2. Déployer la dernière image de `main` (build à partir du repo GitHub).
3. Configurer les variables d'environnement (cf. [`secrets.md`](secrets.md)) — récupération depuis le coffre interne.
4. Pointer le DNS de la production vers la nouvelle plateforme (TTL court à anticiper en temps normal).
5. Vérifier l'application : healthcheck, smoke tests, Sentry.

### Scénario 5 — Indisponibilité prolongée de Scaleway `fr-par`

**Procédure** (PRA cross-region — perte de données ≤ 7 j)

1. Provisionner de nouvelles bases RDB dans une **autre région Scaleway** à partir des copies cross-region (dumps quotidiens 7 j).
2. Adapter `infrastructure/environments/prod/terraform.tfvars` (région, endpoints) et appliquer Terragrunt.
3. Re-pousser les images Airflow vers un nouveau Container Registry de la région de secours.
4. Reprovisionner les buckets S3 et restaurer les contenus depuis le dernier export disponible (snapshots horodatés pour `lvao-opendata`).
5. Mettre à jour `DATABASE_URL` et `AWS_*` côté Scalingo + secrets Airflow.
6. Reprise de service après healthcheck.

> ⚠️ Procédure **non testée régulièrement** à ce jour — à inclure dans les exercices PRA (cf. § Tests).

### Scénario 6 — Compromission de secrets

Procédure de rotation détaillée dans [`secrets.md`](secrets.md). À effectuer dans l'ordre :

1. Révoquer le secret compromis chez l'émetteur (Scaleway, Scalingo, GitHub, PostHog, Notion, Mattermost…).
2. Générer un nouveau secret.
3. Mettre à jour :
   - Variables Scalingo (webapp).
   - `secret_environment_variables` Terragrunt + `terragrunt apply` (Airflow).
   - GitHub Environments `preprod` / `prod` (CI/CD).
   - `terraform.tfvars` local (OpenTofu).
4. Redéployer la webapp et les containers Airflow.
5. Audit Sentry / logs pour détecter une exploitation.
6. Notifier conformément à la politique [SECURITY.md](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/SECURITY.md) si nécessaire.

### Scénario 7 — Reconstruction complète depuis zéro

Tout le socle peut être ré-instancié à partir du seul repo Git + sauvegardes :

1. **Infra** : `cd infrastructure/environments/prod && terragrunt apply --all` (l'état est dans `lvao-terraform-state`).
2. **Images Airflow** : workflow CI/CD `cd.yml` ré-exécuté → build & push sur `ns-qfdmo` → déploiement Scaleway CaaS.
3. **Webapp** : `git push` sur `main` → déploiement Scalingo via `kolok/deploy-to-scalingo`.
4. **Données** : restaurer DB Webapp depuis dump (cf. scénario 1) et reposter contenus S3.
5. **Secrets** : ré-injection depuis le coffre interne ([`secrets.md`](secrets.md)).
6. **DNS** : vérification des enregistrements pointant vers Scalingo / Scaleway.

## Procédure de bascule prod → preprod (palliatif)

En cas d'incident **sur la prod uniquement** et si la preprod est en bon état, la preprod peut être utilisée comme environnement de consultation :

- Communiquer l'URL preprod en dégradé.
- ⚠️ Données potentiellement décalées (sync hebdo `sync_databases.yml`).
- Pas d'écriture utilisateur attendue sur la preprod en dégradé.

## Outils & accès requis

| Outil                                  | Usage en PRA                                         | Détenteurs                         |
| -------------------------------------- | ---------------------------------------------------- | ---------------------------------- |
| Console **Scaleway**                   | Restauration RDB, gestion CaaS, S3, Registry         | Admins projet `longuevieauxobjets` |
| CLI **Scaleway** (`scw`)               | Scripts et automatisation                            | Équipe dev                         |
| Console **Scalingo**                   | Redémarrage, scale, variables d'environnement webapp | Équipe dev (token + clé SSH)       |
| **OpenTofu / Terragrunt**              | Re-provisionnement infrastructure                    | Équipe dev (`terraform.tfvars`)    |
| **GitHub**                             | Code, Actions CI/CD, gestion des Environments        | Équipe dev                         |
| **Mattermost** `lvao-tour-de-controle` | Communication incident                               | Équipe                             |
| **Sentry**                             | Diagnostic erreurs applicatives                      | Équipe dev                         |

## Communication d'incident

| Étape        | Canal                                                    | Contenu                                                   |
| ------------ | -------------------------------------------------------- | --------------------------------------------------------- |
| Détection    | Mattermost `lvao-tour-de-controle` + Sentry + Cockpit    | Premier signalement, hypothèses initiales.                |
| Mobilisation | Mattermost / canal dédié incident                        | Désignation pilote, allocation rôles.                     |
| Pendant      | Mattermost, mises à jour régulières                      | État des actions, ETA reprise.                            |
| Fin          | Mattermost + notification utilisateurs si impact externe | Service rétabli, périmètre concerné, données impactées.   |
| Post-mortem  | PR documentation / canal interne                         | Causes racines, actions correctives, mise à jour PCA/PRA. |

## Tests & maintenance du PRA

> Le **calendrier** et le **journal historique** de ces tests sont centralisés dans [`reviews.md`](reviews.md).

| Test                                | Fréquence cible                  | Action                                                                                                  |
| ----------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Restauration PITR DB Webapp**     | Trimestriel                      | Restaurer un PITR sur une instance jetable et vérifier la cohérence des données.                        |
| **Restauration depuis dump**        | Semestriel                       | Restaurer un dump 7 j sur une instance jetable.                                                         |
| **Récupération objet S3 versionné** | Annuel                           | Supprimer un objet de test sur `qfdmo-interface` et le récupérer via versioning.                        |
| **Re-provisionnement preview**      | À chaque évolution majeure d'IaC | `terragrunt apply --all` puis `destroy` sur l'environnement `preview`.                                  |
| **Sync prod → preprod**             | Hebdo automatique                | Sert de validation continue de la procédure de restauration ([`ci-cd.md`](../infrastructure/ci-cd.md)). |
| **Bascule cross-region**            | À planifier                      | Non testé à ce jour — à intégrer dans les exercices.                                                    |
| **Revue documentaire PRA / PCA**    | Annuelle                         | Mise à jour des RTO/RPO, ajout de scénarios, retour d'expérience post-incidents.                        |

## Limites connues

- **RTO/RPO non contractualisés** avec les fournisseurs — valeurs cibles internes uniquement.
- **Bascule cross-region non répétée** : la procédure existe (sauvegardes cross-region disponibles) mais n'est pas exercée régulièrement.
- **Pas de site de secours chaud** : la reprise après sinistre régional implique un re-provisionnement (RTO de plusieurs heures).
- **Coffre de secrets centralisé** : la procédure de récupération des secrets en cas de perte du poste opérateur principal doit être formalisée séparément.
