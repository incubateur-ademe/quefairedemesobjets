# Architecture applicative

Vue d'ensemble de la plateforme « Que Faire De Mes Objets et Déchets » (QFDMOD), des composants en présence et de leurs interactions.

> **Voir aussi** : [Flux de consolidation des données](data-flow.md), [Services externes](external-services.md), [Provisioning de l'infrastructure](../infrastructure/provisioning.md), [CI/CD](../infrastructure/ci-cd.md), [Monitoring](../infrastructure/monitoring.md), [Sécurité — vue d'ensemble](../security/README.md).

## Diagramme global

```mermaid
flowchart LR
    user(("👤 Utilisateur"))
    integrateur(("🧩 Intégrateur iframe"))
    admin(("🛠️ Admin / Éditeur"))

    subgraph github["GitHub Actions (CI/CD)"]
        direction TB
        ci["Lint + tests"]
        cd["Deploy webapp + Airflow"]
        sync["Sync DB prod → preprod"]
    end

    subgraph Scalingo["☁️ Scalingo (region osc-fr1)"]
        nginx_scalingo["nginx (cache + proxy /ph/)"]
        webapp["🌐 Webapp Django\n(gunicorn, WhiteNoise)"]
        django_worker["⚙️ Worker django-tasks\n(db_worker)"]
    end

    subgraph Scaleway["☁️ Scaleway (region fr-par, projet longuevieauxobjets)"]
        direction TB
        subgraph CaaS["Container as a Service"]
            airflow_webserver["🖥️ Airflow Webserver\n(api-server :8080)"]
            airflow_scheduler["⏰ Airflow Scheduler\n+ dbt"]
            airflow_dag_processor["📁 Airflow DAG Processor\n(+ nginx healthcheck)"]
        end

        subgraph Registry["🐳 Container Registry"]
            ns_qfdmo["namespace ns-qfdmo (privé)"]
        end

        subgraph Databases["🗄️ Bases PostgreSQL 16 (RDB HA)"]
            db_webapp[("DB Webapp\nlvao-{env}-webapp")]
            db_warehouse[("DB Warehouse\nlvao-{env}-warehouse")]
            db_airflow[("DB Airflow\nlvao-{env}-airflow")]
            db_warehouse <-->|"postgres_fdw"| db_webapp
        end

        subgraph S3["📦 Object Storage (S3 fr-par)"]
            s3_medias[("qfdmo-interface\nuploads Django Admin")]
            s3_opendata[("lvao-opendata\nexports CSV")]
            s3_logs[("lvao-{env}-airflow\nlogs Airflow")]
            s3_source[("lvao-data-source\nfichiers Excel")]
            s3_tfstate[("lvao-terraform-state")]
        end
    end

    subgraph monitoring["📈 Monitoring & analytics"]
        sentry["Sentry (beta.gouv)"]
        posthog["PostHog EU"]
        matomo["Matomo (stats.beta.gouv.fr)"]
        cockpit["Scaleway Cockpit (Grafana)"]
        mattermost["Mattermost\nlvao-tour-de-controle"]
        dashlord["Dashlord ADEME"]
    end

    subgraph sources_ext["🌍 Sources & APIs externes"]
        eco_organismes["Éco-organismes & ADEME"]
        ban_geo["BAN / geo.api.gouv.fr"]
        ae_insee["AE / INSEE / La Poste / Koumoul"]
        notion["Notion API"]
        tally["Tally.so"]
    end

    user -->|"HTTPS"| nginx_scalingo
    integrateur -->|"iframe carte/assistant/infotri"| nginx_scalingo
    admin -->|"/admin/, /cms/"| nginx_scalingo
    nginx_scalingo --> webapp
    nginx_scalingo -->|"/ph/*"| posthog

    webapp --> db_webapp
    webapp -->|"enqueue tâches"| django_worker
    django_worker --> db_webapp
    webapp --> s3_medias
    webapp -->|"erreurs"| sentry
    webapp -->|"HogQL stats"| posthog
    webapp -->|"BAN, EPCI"| ban_geo
    webapp -->|"contact form"| notion
    webapp -->|"forms"| tally

    airflow_scheduler --> db_airflow
    airflow_scheduler -->|"ETL writes"| db_webapp
    airflow_scheduler -->|"dbt run/test"| db_warehouse
    airflow_scheduler -->|"export CSV"| s3_opendata
    airflow_scheduler -->|"S3Hook"| s3_source
    airflow_scheduler -->|"ingestion"| eco_organismes
    airflow_scheduler -->|"clone refs"| ae_insee
    airflow_webserver --> db_airflow
    airflow_dag_processor --> db_airflow
    airflow_webserver -.->|"état tâches"| airflow_scheduler
    CaaS -.->|"remote logs"| s3_logs

    cd -->|"git push SSH"| Scalingo
    cd -->|"build & push"| ns_qfdmo
    ns_qfdmo -->|"pull"| CaaS
    sync -->|"restore"| db_webapp

    user -.->|"analytics"| matomo
    Databases -.->|"métriques"| cockpit
    cd -.->|"notif deploy"| mattermost
```

## Cartographie des composants

Pour le détail de chaque brique, suivre le lien correspondant.

### Hébergement applicatif

| Composant                                                    | Hébergeur                                  | Détail / référence                                                                                                               |
| ------------------------------------------------------------ | ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| **Webapp Django** (Gunicorn + WhiteNoise + nginx local)      | Scalingo (`osc-fr1`)                       | [`infrastructure/provisioning.md`](../infrastructure/provisioning.md), [`webapp/README.md`](../webapp/README.md)                 |
| **Worker django-tasks** (`manage.py db_worker`)              | Scalingo (`osc-fr1`, container `worker`)   | [`webapp/django.md`](../webapp/django.md)                                                                                        |
| **Airflow** : webserver, scheduler (avec dbt), DAG processor | Scaleway Container as a Service (`fr-par`) | [`infrastructure/provisioning.md`](../infrastructure/provisioning.md), [`data-platform/airflow.md`](../data-platform/airflow.md) |
| **Container Registry** privé `ns-qfdmo`                      | Scaleway                                   | [`infrastructure/provisioning.md`](../infrastructure/provisioning.md)                                                            |

### Données

| Composant                                                                                                                    | Hébergeur                                             | Détail / référence                                                                                     |
| ---------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **DB Webapp** `lvao-{env}-webapp` (données métier, cache, médias Wagtail, PostGIS)                                           | Scaleway RDB PostgreSQL 16 HA                         | [`db/db_organisation.md`](../db/db_organisation.md), [`db/architecture.md`](../db/architecture.md)     |
| **DB Warehouse** `lvao-{env}-warehouse` (couches dbt)                                                                        | Scaleway RDB                                          | [`db/db_organisation.md`](../db/db_organisation.md), [`data-platform/dbt.md`](../data-platform/dbt.md) |
| **DB Airflow** `lvao-{env}-airflow` (métadonnées)                                                                            | Scaleway RDB                                          | [`data-platform/airflow.md`](../data-platform/airflow.md)                                              |
| Liaison **`postgres_fdw`** Webapp ↔ Warehouse                                                                                | Schémas virtuels `webapp_public` / `warehouse_public` | [`db/db_organisation.md`](../db/db_organisation.md)                                                    |
| **Object Storage** S3 (`qfdmo-interface`, `lvao-opendata`, `lvao-{env}-airflow`, `lvao-data-source`, `lvao-terraform-state`) | Scaleway S3 (`fr-par`)                                | [`infrastructure/provisioning.md`](../infrastructure/provisioning.md)                                  |

### Plateforme data

| Composant                                                               | Référence                                                                                   |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Orchestration **Airflow 3** (`LocalExecutor`, FAB auth, JWT)            | [`data-platform/airflow.md`](../data-platform/airflow.md)                                   |
| **Sources** d'ingestion (éco-organismes, ADEME, API CMA/Pharmacies, S3) | [`data-platform/sources.md`](../data-platform/sources.md)                                   |
| Transformation **dbt** (base/intermediate/marts/exposure)               | [`data-platform/dbt.md`](../data-platform/dbt.md)                                           |
| **Clustering / déduplication**                                          | [`data-platform/clustering-deduplication.md`](../data-platform/clustering-deduplication.md) |

### Webapp

| Composant                                                                                       | Référence                                               |
| ----------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| **Django** + apps métier (`qfdmo`, `qfdmd`, `search`, `data`, `infotri`, `stats`, `dsfr_hacks`) | [`webapp/django.md`](../webapp/django.md)               |
| **Tâches asynchrones** django-tasks (actions admin lourdes, file en base)                       | [`webapp/django.md`](../webapp/django.md)               |
| **API Django-Ninja** (`/api/qfdmo/*`, `/api/stats`)                                             | [`apis/README.md`](../apis/README.md)                   |
| **CMS Wagtail** (surcouche `sites-conformes`)                                                   | [`webapp/README.md`](../webapp/README.md)               |
| **Front** Stimulus + Turbo + Parcel + TypeScript                                                | [`webapp/javascript.md`](../webapp/javascript.md)       |
| **Design system** DSFR + Tailwind (prefix `qf-`)                                                | [`webapp/look-and-feel.md`](../webapp/look-and-feel.md) |
| **Templates** Django                                                                            | [`webapp/templates.md`](../webapp/templates.md)         |

### CI/CD & déploiement

| Composant                                                                               | Référence                                                             |
| --------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Workflows GitHub Actions (review, cd, deploy, sync_databases, dependabot, publish-docs) | [`infrastructure/ci-cd.md`](../infrastructure/ci-cd.md)               |
| Provisioning OpenTofu / Terragrunt                                                      | [`infrastructure/provisioning.md`](../infrastructure/provisioning.md) |

### Observabilité

| Composant                                                          | Référence                                                         |
| ------------------------------------------------------------------ | ----------------------------------------------------------------- |
| Sentry, PostHog, Matomo, Scaleway Cockpit, Mattermost, healthcheck | [`infrastructure/monitoring.md`](../infrastructure/monitoring.md) |
| CodeQL, GitGuardian, Dependabot, Dashlord                          | [`security/README.md`](../security/README.md)                     |

### Sécurité

| Sujet                                | Référence                                                     |
| ------------------------------------ | ------------------------------------------------------------- |
| Inventaire des actifs à protéger     | [`security/inventory.md`](../security/inventory.md)           |
| Prestataires & exigences de sécurité | [`security/providers.md`](../security/providers.md)           |
| Authentification & autorisations     | [`security/authentication.md`](../security/authentication.md) |
| Sécurité réseau                      | [`security/network.md`](../security/network.md)               |
| Gestion des secrets                  | [`security/secrets.md`](../security/secrets.md)               |
| Sauvegardes                          | [`security/backups.md`](../security/backups.md)               |
| Plan de continuité d'activité (PCA)  | [`security/pca.md`](../security/pca.md)                       |
| Plan de reprise d'activité (PRA)     | [`security/pra.md`](../security/pra.md)                       |
| Revues régulières                    | [`security/reviews.md`](../security/reviews.md)               |

```{toctree}
:maxdepth: 2
:hidden:

data-flow.md
external-services.md
```
