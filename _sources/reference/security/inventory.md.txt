# Inventaire des actifs à protéger

Liste des **activités, services et données** du système d'information à protéger, et actions régulières associées.

> **Voir aussi** : [Prestataires](providers.md), [Authentification](authentication.md), [Sécurité réseau](network.md), [Gestion des secrets](secrets.md), [Sauvegardes](backups.md), [PCA](pca.md), [PRA](pra.md), [Architecture applicative](../architecture/README.md).

## Principe

Tous les **applicatifs et bases de données en production** sont considérés comme **à protéger**. Deux niveaux de priorité sont retenus pour orienter l'effort de sécurisation et la fréquence des contrôles :

- **Priorité 1 — Webapp publique** : composants directement exposés au grand public et aux intégrateurs (impact image, RGPD, continuité de service).
- **Priorité 2 — Plateforme data (Airflow)** : composants internes alimentant la webapp (impact différé, rattrapable par re-run).

La documentation du périmètre fonctionnel détaillé reste portée par [`architecture/README.md`](../architecture/README.md). Cet inventaire en est la **lecture sécurité**.

## Priorité 1 — Webapp publique

| Actif                                                    | Type            | Hébergeur                     | Sensibilité                                                  | Référence                                                                                         |
| -------------------------------------------------------- | --------------- | ----------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| **Webapp Django**                                        | Applicatif      | Scalingo (`osc-fr1`)          | Service public (carte, assistant, API, iframes intégrateurs) | [`webapp/README.md`](../webapp/README.md), [`provisioning.md`](../infrastructure/provisioning.md) |
| **Django Admin / CMS Wagtail / `/data/`**                | Applicatif      | Scalingo                      | Outils internes (auth `django.contrib.auth`)                 | [`authentication.md`](authentication.md)                                                          |
| **Worker django-tasks** (`db_worker`)                    | Applicatif      | Scalingo (container `worker`) | Traitement asynchrone des actions admin lourdes (file en DB) | [`webapp/django.md`](../webapp/django.md)                                                         |
| **API REST Django-Ninja** (`/api/qfdmo/*`, `/api/stats`) | Applicatif      | Scalingo                      | Endpoint public en lecture                                   | [`apis/README.md`](../apis/README.md)                                                             |
| **DB Webapp** `lvao-prod-webapp`                         | Base de données | Scaleway RDB PostgreSQL 16 HA | Données métier, cache, médias Wagtail, PostGIS               | [`db/db_organisation.md`](../db/db_organisation.md)                                               |
| **Bucket `qfdmo-interface`**                             | Stockage        | Scaleway S3 (`fr-par`)        | Médias uploadés via Django Admin                             | [`backups.md`](backups.md)                                                                        |

## Priorité 2 — Plateforme data (Airflow)

| Actif                                             | Type            | Hébergeur                                  | Sensibilité                                 | Référence                                                 |
| ------------------------------------------------- | --------------- | ------------------------------------------ | ------------------------------------------- | --------------------------------------------------------- |
| **Airflow Webserver / Scheduler / DAG Processor** | Applicatif      | Scaleway Container as a Service (`fr-par`) | Orchestration des pipelines internes        | [`data-platform/airflow.md`](../data-platform/airflow.md) |
| **DB Warehouse** `lvao-prod-warehouse`            | Base de données | Scaleway RDB                               | Couches dbt (reconstructible par `dbt run`) | [`data-platform/dbt.md`](../data-platform/dbt.md)         |
| **DB Airflow** `lvao-prod-airflow`                | Base de données | Scaleway RDB                               | Métadonnées Airflow (perte tolérable)       | [`data-platform/airflow.md`](../data-platform/airflow.md) |
| **Bucket `lvao-opendata`**                        | Stockage        | Scaleway S3                                | Exports CSV publics + snapshots horodatés   | [`backups.md`](backups.md)                                |
| **Bucket `lvao-data-source`**                     | Stockage        | Scaleway S3                                | Fichiers source (Excel, ingestions)         | [`provisioning.md`](../infrastructure/provisioning.md)    |
| **Bucket `lvao-prod-airflow`**                    | Stockage        | Scaleway S3                                | Logs distants Airflow                       | [`data-platform/airflow.md`](../data-platform/airflow.md) |
| **Container Registry** `ns-qfdmo`                 | Stockage        | Scaleway                                   | Images Docker Airflow (privé)               | [`provisioning.md`](../infrastructure/provisioning.md)    |

## Actifs transverses

| Actif                                                             | Type          | Hébergeur                           | Rôle sécurité                                                            |
| ----------------------------------------------------------------- | ------------- | ----------------------------------- | ------------------------------------------------------------------------ |
| **Bucket `lvao-terraform-state`**                                 | Stockage      | Scaleway S3                         | État OpenTofu (versionné, chiffré) — reconstruction infra à l'identique. |
| **Coffre de secrets** (Scalingo, Terragrunt, GitHub Environments) | Configuration | Scalingo / GitHub / poste opérateur | Variables sensibles (DSN, tokens). Voir [`secrets.md`](secrets.md).      |
| **Code source & IaC**                                             | Repository    | GitHub                              | Code applicatif, infrastructure, documentation, workflows CI/CD.         |

## Actions régulières pour garantir la sécurité

Les actions ci-dessous sont menées de manière récurrente pour maintenir le niveau de sécurité du périmètre listé ci-dessus.

| Action                                                     | Fréquence cible                                  | Outil / référence                                                                      |
| ---------------------------------------------------------- | ------------------------------------------------ | -------------------------------------------------------------------------------------- |
| **Mise à jour des dépendances**                            | Hebdomadaire                                     | Dependabot ([`README.md`](README.md))                                                  |
| **Scan de secrets**                                        | À chaque commit                                  | `detect-secrets` (pre-commit) + GitGuardian (CI) ([`secrets.md`](secrets.md))          |
| **Analyse statique du code**                               | À chaque PR                                      | CodeQL, Ruff, ESLint, Black, Prettier ([`README.md`](README.md))                       |
| **Audit sécurité externe**                                 | Continu                                          | Dashlord ADEME ([dashlord.incubateur.ademe.fr](https://dashlord.incubateur.ademe.fr/)) |
| **Surveillance des erreurs applicatives**                  | Continu                                          | Sentry ([`monitoring.md`](../infrastructure/monitoring.md))                            |
| **Surveillance infrastructure**                            | Continu                                          | Scaleway Cockpit (Grafana) ([`monitoring.md`](../infrastructure/monitoring.md))        |
| **Healthcheck post-déploiement**                           | À chaque deploy                                  | `HEALTHCHECK_URLS` + notification Mattermost ([`pca.md`](pca.md))                      |
| **Test de restauration PITR DB Webapp**                    | Trimestriel                                      | [`pra.md`](pra.md) §Tests                                                              |
| **Test de restauration depuis dump**                       | Semestriel                                       | [`pra.md`](pra.md) §Tests                                                              |
| **Test de récupération objet S3 versionné**                | Annuel                                           | [`pra.md`](pra.md) §Tests                                                              |
| **Revue documentaire PCA / PRA**                           | Annuelle                                         | [`pca.md`](pca.md), [`pra.md`](pra.md)                                                 |
| **Revue de cet inventaire** (activités, services, données) | **Annuelle au minimum, ou en cas de changement** | [`reviews.md`](reviews.md)                                                             |

## Revue de l'inventaire

L'inventaire ci-dessus doit être **vérifié au moins une fois par an**, ou plus tôt en cas de changement significatif (ajout/retrait d'un service, changement d'hébergeur, nouvelle base de données, nouveau bucket, etc.).

À chaque revue :

1. Vérifier que tous les actifs en production sont listés.
2. Confirmer la priorité (1 ou 2) et la sensibilité.
3. Mettre à jour les liens vers la documentation associée si elle a évolué.
4. Consigner la revue dans le **journal centralisé** : [`reviews.md`](reviews.md) §Inventaire des actifs.

> Le calendrier et l'historique de toutes les revues récurrentes (inventaire, PCA, PRA, tests de restauration) sont centralisés dans [`reviews.md`](reviews.md).
