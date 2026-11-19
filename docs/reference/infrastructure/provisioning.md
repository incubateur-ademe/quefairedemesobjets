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
│   ├── root.hcl                     -> backend, provider, secrets: every stack
│   ├── _envcommon/
│   │   └── database.hcl             -> what the stack is in every environment
│   ├── prod/
│   │   ├── env.hcl                  -> what the stacks share about prod (domain…)
│   │   └── database/
│   │       ├── terragrunt.hcl       -> includes both, adds what is prod's own
│   │       └── secrets.example.json -> keys of the stack's secret
│   ├── preprod/
│   └── preview/
└── modules/
    ├── database/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── provider/
```

A stack is described once, in `_envcommon/<stack>.hcl`: its module, its dependencies and the inputs that are the same everywhere. The `terragrunt.hcl` of an environment only holds what differs there (sizing, names). A stack that exists in a single environment (`metabase_containers`, `container_registry`) keeps everything in its `terragrunt.hcl`.

#### Configuration

No local `terraform.tfvars` is needed.

1. Export the Scaleway credentials, in your shell or in the repo root `.env`:
   `SCW_ACCESS_KEY`, `SCW_SECRET_KEY`, `SCW_DEFAULT_PROJECT_ID`,
   `SCW_DEFAULT_ORGANIZATION_ID`. `root.hcl` passes them to every stack.
2. The other secrets of a stack live in Scaleway Secret Manager: one secret
   per stack, named after it at path `/terraform/<ENV>`, holding a JSON object
   with the keys of the stack's `secrets.example.json`. `root.hcl` reads it on
   every `terragrunt` run, through `scripts/infrastructure/stack_secrets.sh`
   (needs the `scw` CLI and `jq`). A stack without a `secrets.example.json`
   has no secret.

Your API key needs `SecretManagerReadOnly` and `SecretManagerSecretAccess` to
plan or apply, and `SecretManagerFullAccess` to change a secret.

To read or change the secret of a stack:

```sh
make -C infrastructure secrets-show ENV=preprod STACK=database > infrastructure/environments/preprod/database/secrets.json
# edit secrets.json (gitignored), then
make -C infrastructure secrets-push ENV=preprod STACK=database
rm infrastructure/environments/preprod/database/secrets.json
```

`secrets-push` creates the secret if needed, adds a version and disables the
previous one. It refuses a file whose keys differ from `secrets.example.json`:
a new secret input is added there first.

An input set in a stack's `terragrunt.hcl` wins over its secret, and a local
`terraform.tfvars` wins over both.

Only secrets go there. A value that is not one (a user name, a database name,
an image tag) is written in the stack's `terragrunt.hcl`, or read from the
output of the stack that creates the resource.

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

#### Stacks deployed by the CI

`airflow_containers` and `nginx_containers` are applied by the CI on every deployment, with the image tag passed as `IMAGE_TAG` (see [CI/CD](ci-cd.md)). To plan or apply one by hand without changing the image, check that no deployment is in progress, then:

```sh
make -C infrastructure live-plan ENV=<ENV> STACK=airflow_containers
make -C infrastructure live-apply ENV=<ENV> STACK=airflow_containers
```

These pass as `IMAGE_TAG` the tag of the container running now, read from Scaleway. The `registry_image` output comes from the state, which lags behind an image deployed outside Terragrunt.

Without `IMAGE_TAG` the plan fails instead of deploying a placeholder image.

## Composants déployés

> **Voir aussi** : [Architecture applicative](../architecture/README.md), [Bases de données](../db/db_organisation.md), [Airflow](../data-platform/airflow.md), [Sauvegardes](../security/backups.md), [PCA](../security/pca.md), [PRA](../security/pra.md).

### Scalingo (région `osc-fr1`)

| Composant               | Détail                                                                                                                                                                                                                                                    |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Webapp Django**       | Application web principale exposée aux utilisateurs (front public, back-office Django Admin, CMS Wagtail). Servie par **Gunicorn** sur socket Unix, fichiers statiques via **WhiteNoise** (`CompressedManifestStaticFilesStorage`).                       |
| **Buildpacks**          | `apt`, `node`, `python`, `nginx` (ordre défini dans `.buildpacks` à la racine du monorepo). Pas de `PROJECT_DIR` : le slug est la racine ; `uv.lock` racine + dépendance workspace webapp.                                                                |
| **Procfile**            | `web: bash bin/start` — Gunicorn (`webapp/`) + nginx ; `worker` — `manage.py db_worker` dans `webapp/` ; `postdeploy` — migrations / cache.                                                                                                               |
| **Worker django-tasks** | Container Scalingo `worker` (Procfile). Traite les tâches enqueueées en base PostgreSQL (même `DATABASE_URL` que le web). Voir [`webapp/django.md`](../webapp/django.md).                                                                                 |
| **nginx Scalingo**      | Couche de cache devant Gunicorn (`servers.conf.erb`), proxy `/ph/*` vers PostHog (analytics first-party), bypass cache via cookie `logged_in` (posé par `RequestEnhancementMiddleware`), `Vary: Sec-Fetch-Dest` (distingue iframe vs navigation directe). |
| **Base de données**     | La webapp cible la DB Scaleway `lvao-{env}-webapp` via `DATABASE_URL` (pas d'add-on PostgreSQL Scalingo).                                                                                                                                                 |
| **Cache applicatif**    | `django.core.cache.backends.db.DatabaseCache` (table `qf_django_cache`). **Pas de Redis** : tous les caches sont stockés en base.                                                                                                                         |
| **Médias**              | Délégués à Scaleway Object Storage (`django-storages` + `boto3`).                                                                                                                                                                                         |

### Scaleway (région `fr-par`, projet `longuevieauxobjets`)

Toutes les ressources suivent la nomenclature `lvao-{env}-{nom}` où `env ∈ {prod, preprod, preview}`.

#### Container as a Service (CaaS)

Trois Serverless Containers distincts pour Airflow 3 (`apache/airflow:slim-<version>-python3.12`, version de `apache-airflow` dans `data-platform/pyproject.toml`), construits via Dockerfiles dédiés, plus un gateway nginx par environnement :

| Container                    | Image                              | Rôle                                                                                                                                                                                                                     |
| ---------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `lvao-airflow-webserver`     | `airflow-webserver.Dockerfile`     | Interface UI/API Airflow (`airflow api-server`, port 8080). Création du compte admin au premier démarrage via `_AIRFLOW_WWW_USER_*`.                                                                                     |
| `lvao-airflow-scheduler`     | `airflow-scheduler.Dockerfile`     | Orchestrateur (`LocalExecutor`). Embarque le runtime **dbt** (`dbt deps`), `gdal-bin`, le CLI Scaleway, `jq`, `unzip` pour les pipelines ETL.                                                                            |
| `lvao-airflow-dag-processor` | `airflow-dag-processor.Dockerfile` | Parsing isolé des DAGs avec nginx en façade pour le healthcheck.                                                                                                                                                         |
| `lvao-nginx`                 | `nginx/nginx.Dockerfile`           | Reverse-proxy public. Les CNAME wildcard `*.quefairedemesobjets.ademe.fr` (prod) et `*.preprod.quefairedemesobjets.ademe.fr` (preprod) pointent vers ce container, qui route `airflow.` / `metabase.` vers les backends. |

Voir [`data-platform/airflow.md`](../data-platform/airflow.md) pour le détail de la configuration runtime (auth manager, JWT, métadonnées).

#### Container Registry

Namespace privé `ns-qfdmo` — héberge les images Docker des containers Airflow, du gateway nginx et de la webapp preview (push par la CI, pull par les Serverless Containers).

#### Bases de données (RDB PostgreSQL 16 HA)

| Base de données | Nom Scaleway                                       | Usage                                                                                                                                                         |
| --------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DB Webapp       | Instance `lvao-{env}-webapp` / base `webapp`       | Données applicatives (acteurs, propositions de service, configurations carte, utilisateurs Wagtail/Django, cache, médias Wagtail). Extension PostGIS activée. |
| DB Warehouse    | Instance `lvao-{env}-warehouse` / base `warehouse` | Tables analytiques produites par **dbt**. Schéma `webapp_public` consommé en source via `postgres_fdw`.                                                       |
| DB Airflow      | Instance `lvao-{env}-warehouse` / base `airflow`   | Métadonnées Airflow (état des DAGs, XComs, logs courts). Nettoyée quotidiennement par le DAG `airflow_cleanup_db`.                                            |
| DB Metabase     | Instance `lvao-{env}-warehouse` / base `metabase`  | Base applicative Metabase (optionnelle, provisionnée si `metabase_db_username` est défini).                                                                   |

Connexions clientes en `sslmode=require`. Voir [`db/db_organisation.md`](../db/db_organisation.md) pour la liaison `postgres_fdw` et [`security/backups.md`](../security/backups.md) pour la stratégie de sauvegarde.

Pour faire tourner les mots de passe (`webapp_db_password`, `warehouse_db_password`, `airflow_db_password`), suivre [Rotating database passwords](../../how-to/infrastructure/rotate_db_passwords.md).

#### Object Storage (S3 `fr-par`)

| Bucket                 | Connexion Airflow | Usage                                                                                                                                                                                                                                                                                       |
| ---------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `qfdmo-interface`      | —                 | Fichiers (images) uploadés depuis l'interface **Django Admin** de la webapp : `logos/`, `labels/`, `pictos/`, `config/groupeaction/icones/`, images Wagtail.                                                                                                                                |
| `lvao-opendata`        | `s3data`          | Export CSV opendata des acteurs (`acteurs.csv` permanent + snapshot horodaté `YYYYMMDDHHMMSS.csv`, ACL `public-read`) et des fiches (`fiches/produits.csv`, `fiches/consignes.csv` permanents + copies horodatées `YYYYMMDDHHMMSS_produits.csv`). Produit par le DAG `export_opendata_dag`. |
| `lvao-data-source`     | `s3data`          | Fichiers Excel ad-hoc consommés par le DAG `source-s3`.                                                                                                                                                                                                                                     |
| `lvao-{env}-airflow`   | `scalewaylogs`    | Remote logs Airflow (`AIRFLOW__LOGGING__REMOTE_LOGGING=true`).                                                                                                                                                                                                                              |
| `lvao-terraform-state` | —                 | Backend OpenTofu/Terragrunt (versionné, chiffré).                                                                                                                                                                                                                                           |
