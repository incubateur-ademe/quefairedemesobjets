# Provisioning the infrastructure

This OpenTofu configuration manages the QueFaireDeMesObjets infrastructure on Scaleway.

## Scaleway

All resources on Scaleway are provisioned in the organization `Incubateur ADEME (Pathtech)` and the project `longuevieauxobjets`.

All resources are named following the pattern `lvao-{env}-{explicit-name}` (for example: `lvao-prod-webapp-db`).

## OpenTofu & Terragrunt

We use OpenTofu, the open-source version of `Terraform`, to automate infrastructure provisioning. [Follow the documentation](https://opentofu.org/docs/intro/install/) to install OpenTofu.

[Terragrunt](https://terragrunt.gruntwork.io/) is used alongside OpenTofu to keep the configuration DRY. [Follow the documentation](https://terragrunt.gruntwork.io/docs/getting-started/install/) to install Terragrunt.

The configuration is defined in the `infrastructure` directory.

### Prerequisites

Install and configure the Scaleway CLI by following [Scaleway's instructions](https://www.scaleway.com/en/docs/scaleway-cli/quickstart/).

Make sure you have administration rights on the project targeted by this infrastructure plan.

### IaC: Infrastructure as Code

#### Structure

```
infrastructure/
├── environments/
│   ├── prod/
│   │   ├── terragrunt.hcl
│   │   ├── terraform.tfvars.example
│   │   └── terraform.tfvars -> not versioned
│   ├── preprod/
│   └── preview/
└── modules/
    ├── database/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── provider/
```

#### Configuration

1. Copy `environments/<ENV>/terraform.tfvars.example` to `terraform.tfvars`.
2. Edit the values in `terraform.tfvars` with your information:
   - `project_id`: Scaleway project ID
   - `organization_id`: Scaleway organization ID
   - `db_password`: secure password for the database
   - …

### Execution

#### tfstate

⚠️ The Terraform state is stored in a Scaleway S3 bucket: `s3://lvao-terraform-state`.

#### Per environment

The `preview` environment is used to test our IaC project. We intentionally destroy the infrastructure created in this environment once the Terraform configuration has been tested.

For each environment:

- **Preprod**: `infrastructure/environments/preprod` at the repository root
- **Prod**: `infrastructure/environments/prod` at the repository root

Change directory to `infrastructure/environments/<ENV>` and run:

```sh
terragrunt init -reconfigure --all
```

```sh
terragrunt plan --all
```

```sh
terragrunt apply --all
```

For each command, the environment must be specified.

## Composants déployés

> **Voir aussi** : [Architecture applicative](../architecture/README.md), [Bases de données](../db/db_organisation.md), [Airflow](../data-platform/airflow.md), [Sauvegardes](../security/backups.md), [PCA](../security/pca.md), [PRA](../security/pra.md).

### Scalingo (région `osc-fr1`)

| Composant            | Détail                                                                                                                                                                                                                                                    |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Webapp Django**    | Application web principale exposée aux utilisateurs (front public, back-office Django Admin, CMS Wagtail). Servie par **Gunicorn** sur socket Unix, fichiers statiques via **WhiteNoise** (`CompressedManifestStaticFilesStorage`).                       |
| **Buildpacks**       | `apt`, `node`, `python`, `nginx` (ordre défini dans `webapp/.buildpacks`).                                                                                                                                                                                |
| **Procfile**         | `web: bash bin/start` — lance Gunicorn + nginx local.                                                                                                                                                                                                     |
| **nginx Scalingo**   | Couche de cache devant Gunicorn (`servers.conf.erb`), proxy `/ph/*` vers PostHog (analytics first-party), bypass cache via cookie `logged_in` (posé par `RequestEnhancementMiddleware`), `Vary: Sec-Fetch-Dest` (distingue iframe vs navigation directe). |
| **Base de données**  | La webapp cible la DB Scaleway `lvao-{env}-webapp` via `DATABASE_URL` (pas d'add-on PostgreSQL Scalingo).                                                                                                                                                 |
| **Cache applicatif** | `django.core.cache.backends.db.DatabaseCache` (table `qf_django_cache`). **Pas de Redis** : tous les caches sont stockés en base.                                                                                                                         |
| **Médias**           | Délégués à Scaleway Object Storage (`django-storages` + `boto3`).                                                                                                                                                                                         |

### Scaleway (région `fr-par`, projet `longuevieauxobjets`)

Toutes les ressources suivent la nomenclature `lvao-{env}-{nom}` où `env ∈ {prod, preprod, preview}`.

#### Container as a Service (CaaS)

Trois Serverless Containers distincts pour Airflow 3 (`apache/airflow:slim-3.1.7-python3.12`), construits via Dockerfiles dédiés :

| Container                    | Image                              | Rôle                                                                                                                                          |
| ---------------------------- | ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `lvao-airflow-webserver`     | `airflow-webserver.Dockerfile`     | Interface UI/API Airflow (`airflow api-server`, port 8080). Création du compte admin au premier démarrage via `_AIRFLOW_WWW_USER_*`.          |
| `lvao-airflow-scheduler`     | `airflow-scheduler.Dockerfile`     | Orchestrateur (`LocalExecutor`). Embarque le runtime **dbt** (`dbt deps`), `gdal-bin`, le CLI Scaleway, `jq`, `unzip` pour les pipelines ETL. |
| `lvao-airflow-dag-processor` | `airflow-dag-processor.Dockerfile` | Parsing isolé des DAGs avec nginx en façade pour le healthcheck.                                                                              |

Voir [`data-platform/airflow.md`](../data-platform/airflow.md) pour le détail de la configuration runtime (auth manager, JWT, métadonnées).

#### Container Registry

Namespace privé `ns-qfdmo` — héberge les images Docker des 3 containers Airflow (push par la CI, pull par les Serverless Containers).

#### Bases de données (RDB PostgreSQL 16 HA)

| Base de données | Nom Scaleway           | Usage                                                                                                                                                         |
| --------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DB Webapp       | `lvao-{env}-webapp`    | Données applicatives (acteurs, propositions de service, configurations carte, utilisateurs Wagtail/Django, cache, médias Wagtail). Extension PostGIS activée. |
| DB Warehouse    | `lvao-{env}-warehouse` | Tables analytiques produites par **dbt**. Schéma `webapp_public` consommé en source via `postgres_fdw`.                                                       |
| DB Airflow      | `lvao-{env}-airflow`   | Métadonnées Airflow (état des DAGs, XComs, logs courts). Nettoyée quotidiennement par le DAG `airflow_cleanup_db`.                                            |

Connexions clientes en `sslmode=require`. Voir [`db/db_organisation.md`](../db/db_organisation.md) pour la liaison `postgres_fdw` et [`security/backups.md`](../security/backups.md) pour la stratégie de sauvegarde.

#### Object Storage (S3 `fr-par`)

| Bucket                 | Connexion Airflow | Usage                                                                                                                                                            |
| ---------------------- | ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `qfdmo-interface`      | —                 | Fichiers (images) uploadés depuis l'interface **Django Admin** de la webapp : `logos/`, `labels/`, `pictos/`, `config/groupeaction/icones/`, images Wagtail.     |
| `lvao-opendata`        | `s3data`          | Export CSV opendata des acteurs (`acteurs.csv` permanent + snapshot horodaté `YYYYMMDDHHMMSS.csv`, ACL `public-read`). Produit par le DAG `export_opendata_dag`. |
| `lvao-data-source`     | `s3data`          | Fichiers Excel ad-hoc consommés par le DAG `source-s3`.                                                                                                          |
| `lvao-{env}-airflow`   | `scalewaylogs`    | Remote logs Airflow (`AIRFLOW__LOGGING__REMOTE_LOGGING=true`).                                                                                                   |
| `lvao-terraform-state` | —                 | Backend OpenTofu/Terragrunt (versionné, chiffré).                                                                                                                |
