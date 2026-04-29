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

## Preview environment: webapp + nginx + airflow

The `preview` environment runs the full QFDMO stack (Django webapp, nginx ingress, Airflow scheduler/webserver) on Scaleway Serverless Containers. It is intended for end-to-end validation before preprod.

### One-time bootstrap

#### 1. Build & push images

The webapp and nginx images must be present in `rg.fr-par.scw.cloud/ns-qfdmo/` before the first apply. Trigger the workflow manually:

```sh
gh workflow run _webapp-build-and-push-docker.yml \
  -f image_tag=preview \
  -f environment=preview
```

This pushes:

- `rg.fr-par.scw.cloud/ns-qfdmo/webapp:preview` (Django + gunicorn)
- `rg.fr-par.scw.cloud/ns-qfdmo/webapp-nginx:preview` (reverse proxy)

The Airflow images (`airflow-scheduler:preview`, `airflow-webserver:preview`) are produced by `_airflow-build-and-push-docker.yml` the same way.

#### 2. Create runtime secrets in Scaleway Secret Manager

Runtime secrets are read from Scaleway Secret Manager at `tofu apply` time via `data.scaleway_secret_version`. Per-environment isolation comes from the **Scaleway project** (one project per env), so the secrets have **bare names** identical from one env to the next — there is no `lvao-preview-` or `lvao-prod-` prefix on secret names.

Create them once per env with the `scw` CLI, ensuring `scw config` points at the right project:

```sh
# One per secret. The value comes from your password manager — never typed
# into shell history. Repeat for each name listed below.
scw secret secret create name=SECRET_KEY
SECRET_ID=$(scw secret secret list name=SECRET_KEY -o json | jq -r '.[0].id')
op read 'op://infra/preview/django_secret_key' \
  | scw secret version create secret-id=$SECRET_ID data=-
```

Required secret names (consumed by `container_webapp` and, where applicable, by the airflow scheduler when `use_secret_manager = true`):

- `SECRET_KEY`
- `DATABASE_URL`
- `DB_WAREHOUSE`
- `DB_WEBAPP_SAMPLE`
- `AWS_ACCESS_KEY_ID` (also read by airflow when `use_secret_manager = true`)
- `AWS_SECRET_ACCESS_KEY` (also read by airflow)
- `SENTRY_DSN` (also read by airflow)
- `POSTHOG_PERSONAL_API_KEY` (also read by airflow)
- `NOTION_TOKEN` (also read by airflow)
- `ASSISTANT_POSTHOG_KEY`
- `CARTE_POSTHOG_KEY`

For the DB seed script (`scripts/restore_prod_to_preview.sh`), two more secrets — and these necessarily live in **different** Scaleway projects (prod and preview) but use bare names:

- in the **prod** project: `DATABASE_URL_RO` — read-only conn string to prod
- in the **preview** project: `DATABASE_URL` — admin conn string to preview (same secret as the runtime one above)

#### 3. Set Scaleway API credentials in your shell

```sh
export TF_VAR_access_key="$(op read 'op://infra/scaleway/access_key')"
export TF_VAR_secret_key="$(op read 'op://infra/scaleway/secret_key')"
```

#### 4. Set Airflow secrets as TF*VAR*\* (one-time, only on first preview apply)

The Airflow container module currently takes its secrets as direct Terragrunt inputs, so they need to be in the operator's shell:

```sh
export TF_VAR_AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="$(op read 'op://infra/preview/airflow_db')"
export TF_VAR_AIRFLOW_CONN_WEBAPP_DB="$(op read 'op://infra/preview/airflow_webapp_conn')"
export TF_VAR_DATABASE_URL="$(op read 'op://infra/preview/database_url')"
# ... see infrastructure/environments/preview/container/terragrunt.hcl for the full list
```

(Eventually we'll migrate Airflow to Secret Manager too, mirroring the webapp.)

#### 5. Apply, in dependency order

```sh
cd infrastructure/environments/preview
terragrunt run-all init
terragrunt run-all plan
terragrunt run-all apply
```

Order: `database` → `object_storage` + `database_sample` → `container` (airflow, also creates the namespace reused by webapp/nginx) → `container_webapp` → `container_nginx`.

#### 6. Seed the preview database from prod

The script reads `DATABASE_URL_RO` from the prod Scaleway project and `DATABASE_URL` from the preview project, so it needs both project IDs:

```sh
export SCW_PROD_PROJECT_ID="<uuid of the prod Scaleway project>"
export SCW_PREVIEW_PROJECT_ID="a279f7ac-06ce-4236-9d78-51298d8d72ed"
make db-restore-preview-from-prod
```

This script (`scripts/restore_prod_to_preview.sh`) runs `pg_dump` against prod, drops the preview public schema, and `pg_restore`s into preview. Connection strings are pulled from Scaleway Secret Manager — never from disk.

#### 7. (Optional) Update the webapp's BASE_URL once the nginx public URL is known

After the first nginx apply, find its public URL:

```sh
scw container container list -o json \
  | jq -r '.[] | select(.name=="lvao-preview-nginx") | .domain_name'
```

Then re-apply the webapp with that URL set:

```sh
export TF_VAR_PREVIEW_BASE_URL="https://<that-domain>"
terragrunt apply --terragrunt-working-dir container_webapp
```

### Rotating a secret

```sh
op read 'op://infra/preview/django_secret_key' \
  | scw secret version create secret-id=<id> data=-
# Then trigger a redeploy so the container picks up the new version:
terragrunt apply --terragrunt-working-dir container_webapp
```

The previous version stays accessible in Secret Manager for rollback.
