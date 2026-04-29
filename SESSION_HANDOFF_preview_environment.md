# Session handoff — Terraforming the preview environment on Scaleway

> **For:** the next Claude (or human) picking up this work
> **From:** session ending 2026-04-29, branch `deploy_to_scaleway`
> **Status:** Implementation complete and uncommitted. Not yet applied. Code review surfaced 6 blockers, 3 fixed; 3 still open. See "Outstanding" section.

## 1. Goal

Stand up a **full QFDMO preview stack on Scaleway Serverless Containers**: Django webapp + nginx ingress + Airflow scheduler/webserver + Postgres RDB instances + S3 buckets, all driven by **OpenTofu + Terragrunt applied locally** from the operator's laptop. Preview is a faithful clone of prod for end-to-end validation before promoting to preprod.

User's original requirements (verbatim):

- Terraform applied locally; operator has `scw` CLI and `tofu`.
- Work in `infrastructure/environments/preview/`.
- Reuse Airflow modules at `infrastructure/modules/container/airflow-{scheduler,webserver}.tf`.
- New webapp container from `webapp/Dockerfile` (multi-stage Node 24 + Python 3.12, gunicorn on port 8000).
- New nginx container from `webapp/nginx/Dockerfile` (renders `webapp/servers.conf.erb` via ERB), publicly fronts the webapp.
- All resources in Scaleway project `a279f7ac-06ce-4236-9d78-51298d8d72ed`.
- DB seeded by an operator script (`pg_dump prod` → `pg_restore preview`).
- Secure tfvars/secrets approach — operator wants to start using **Scaleway Secret Manager**.
- Healthcheck on `GET /` returning 200.

## 2. Key decisions made (don't relitigate without good reason)

| Topic                               | Decision                                                                                                                                                                                          | Why                                                                                                                                      |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Webapp image build                  | New GitHub Actions workflow `_webapp-build-and-push-docker.yml`, mirroring the airflow one. Pushes `rg.fr-par.scw.cloud/ns-qfdmo/webapp:<tag>` and `webapp-nginx:<tag>`.                          | Reproducible; no manual `docker push`.                                                                                                   |
| Nginx image                         | Reuse `webapp/nginx/Dockerfile` (context `webapp/`), pushed as `webapp-nginx:preview`.                                                                                                            | Same templating as prod (ERB-rendered `servers.conf.erb`).                                                                               |
| Domain & TLS                        | Scaleway-provided `*.functions.fnc.fr-par.scw.cloud` URL. nginx listens HTTP on `$PORT=8080`; Scaleway terminates TLS at the edge.                                                                | Simplest for preview. No custom DNS yet.                                                                                                 |
| Secrets                             | **Scaleway Secret Manager** as source of truth. Operator's Scaleway API keys come from shell (`TF_VAR_access_key`, `TF_VAR_secret_key`) read from a password manager. **No plaintext in tfvars.** | User explicitly chose this. Audit trail + per-version rollback.                                                                          |
| Secret naming                       | **Bare names** (`SECRET_KEY`, `DATABASE_URL`, etc.) without env prefix. Per-env isolation comes from the **Scaleway project**, not the secret name.                                               | User pushed for this — keeps modules portable across envs. Defaults live IN the modules.                                                 |
| Module shape                        | Two **new** modules: `modules/container_webapp/` and `modules/container_nginx/`. The existing `modules/container/` stays Airflow-only and was extended with optional inputs.                      | Separation of concerns; airflow module signature stays backwards-compatible.                                                             |
| Namespace                           | Stays inside `modules/container/` (NOT extracted). The airflow module owns the `scaleway_container_namespace`; webapp/nginx modules consume it via `dependency.container.outputs.namespace_id`.   | Tried to extract it, **rolled back** because the move would have caused state-level destroy/recreate of preprod/prod airflow containers. |
| Bucket strategy                     | `modules/object_storage/` extended with a gated `webapp` bucket (`var.create_webapp_bucket`, default `false`). For preview only, `create_webapp_bucket = true`.                                   | Avoid surprise additions when preprod/prod next apply.                                                                                   |
| Airflow `AWS_STORAGE_BUCKET_NAME`   | Points to the **airflow** bucket (`lvao-preview-airflow`), NOT the webapp media bucket.                                                                                                           | User chose "Dedicated airflow data bucket" — keeps DAG writes separate from Wagtail media.                                               |
| Webapp `BASE_URL` for preview       | **Empty string default.** To be populated later (operator decision) once the public nginx URL is decided.                                                                                         | User said "BASE_URL will be populated afterward, set an empty default for now". Avoids a circular dependency between webapp ↔ nginx.     |
| `ALLOWED_HOSTS` for preview         | `.functions.fnc.fr-par.scw.cloud,.containers.fnc.fr-par.scw.cloud` (Django leading-dot wildcards).                                                                                                | Covers nginx public URL + internal webapp URL + healthcheck origin.                                                                      |
| Bootstrap pattern                   | Operator creates secrets out-of-band via `scw secret` CLI before the first `tofu apply`. Terraform only **reads** via `data.scaleway_secret_version` — never writes secret values.                | Cleanest separation; values never flow through `tofu` or tfstate.                                                                        |
| `encrypt = true` on tfstate backend | **Reverted** by the user back to `encrypt = false`. Don't flip it back.                                                                                                                           | The user reverted this manually. Honor it.                                                                                               |
| State backend                       | S3 at `s3.fr-par.scw.cloud`, bucket `lvao-terraform-state`.                                                                                                                                       | Existing pattern — unchanged.                                                                                                            |

## 3. What was implemented this session

### 3.1 Modified `root.hcl` and `variables.tf`

- `infrastructure/environments/root.hcl`:
  - Set `project_id = "a279f7ac-06ce-4236-9d78-51298d8d72ed"` in inputs (was `[project_id]` placeholder).
  - Removed unused `organization_id` input.
  - Added `project_id = var.project_id` to the generated `provider "scaleway"` block.
  - **`encrypt = false`** on the S3 backend was kept (user's choice).
- `infrastructure/environments/variables.tf`: removed unused `organization_id` variable.

### 3.2 Modified `modules/container/` (airflow) — additive only

| File                   | Change                                                                                                                                                                                                                                                          |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `variables.tf`         | Added optional `BASE_URL`, `ALLOWED_HOSTS`, `AWS_S3_REGION_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_STORAGE_BUCKET_NAME` (all `default = ""`), `use_secret_manager` (`default = false`), 5 `secret_name_*` vars defaulting to bare names (`AWS_ACCESS_KEY_ID`, etc.). |
| `outputs.tf` (new)     | Exposes `namespace_id` and `namespace_name` so webapp/nginx modules can reuse the namespace.                                                                                                                                                                    |
| `secrets.tf` (new)     | `data.scaleway_secret` + `data.scaleway_secret_version` for 5 webapp secrets. Gated by `use_secret_manager`. When off (preprod/prod default), `local.webapp_secrets = {}` and no API calls happen.                                                              |
| `airflow-scheduler.tf` | `environment_variables` and `secret_environment_variables` now use `merge(...)` to conditionally fold in the new webapp env vars (only when non-empty) and `local.webapp_secrets`. Webserver was NOT changed (DAGs run on the scheduler).                       |

**This is backwards-compatible for preprod/prod.** Their next apply should be a no-op — all new variables default to `""`/`false`/empty set.

### 3.3 Modified `modules/object_storage/` — additive only

- `webapp.tf` (new): `scaleway_object_bucket "webapp"` named `${prefix}-${environment}-webapp`, gated by `var.create_webapp_bucket = false`.
- `outputs.tf` (new): `airflow_bucket_name`, `webapp_bucket_name` (uses `try(...)` so empty when bucket isn't created).
- `variables.tf`: added `create_webapp_bucket` (default `false`).

### 3.4 New module `modules/container_webapp/`

- `main.tf` — `scaleway_container "webapp"`, **private**, port 8000, healthcheck `GET /`, scale 0→1 (scale-to-zero). Reads `secret_environment_variables = local.secrets`.
- `secrets.tf` — `data.scaleway_secret_version` for 11 secrets (SECRET_KEY, DATABASE_URL, DB_WAREHOUSE, DB_WEBAPP_SAMPLE, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, SENTRY_DSN, POSTHOG_PERSONAL_API_KEY, NOTION_TOKEN, ASSISTANT_POSTHOG_KEY, CARTE_POSTHOG_KEY).
- `variables.tf` — all `secret_name_*` default to bare names; `base_url` defaults to `""`.
- `outputs.tf` — `container_id`, `container_name`, `domain_name` (used by nginx as upstream).

### 3.5 New module `modules/container_nginx/`

- `main.tf` — `scaleway_container "nginx"`, **public**, port 8080, healthcheck `GET /` (validates the whole chain through to webapp), scale 1→1 (always on). Hardcodes `UPSTREAM_SCHEME=https` because Scaleway internal endpoints are HTTPS-only.
- `variables.tf` — `legacy_site_vitrine_domain` defaults to `""` (skip legacy redirect for preview).
- `outputs.tf` — `domain_name` (the public ingress URL).

### 3.6 Patched `webapp/servers.conf.erb`

Added an ERB local at the top:

```erb
<%
  upstream_scheme = ENV["UPSTREAM_SCHEME"] == "https" ? "https" : "http"
  upstream_host   = ENV["UPSTREAM_HOST"] || "unix:/tmp/gunicorn.sock"
  upstream_sni    = upstream_host.sub(/:\d+\z/, "")
%>
```

Both `proxy_pass` lines now use `<%= upstream_scheme %>://gunicorn`, and an `<% if upstream_scheme == "https" %>` block injects `proxy_ssl_server_name on;`, `proxy_ssl_name <%= upstream_sni %>;`, and `proxy_set_header Host <%= upstream_sni %>;`. **Default behavior (no `UPSTREAM_SCHEME` set) is unchanged** — local docker-compose still works exactly as before.

### 3.7 Preview env terragrunt entries

```
infrastructure/environments/preview/
├── database/                # already existed; only tfvars.example cleaned up
├── object_storage/          # NEW — sets create_webapp_bucket = true
├── container/               # NEW (airflow); use_secret_manager = true
├── container_webapp/        # NEW; reads namespace from container, bucket from object_storage
└── container_nginx/         # NEW; reads namespace from container, upstream from container_webapp
```

Apply order is enforced by `dependency` blocks. `terragrunt run-all apply` resolves: database → object_storage → container (airflow, also creates namespace) → container_webapp → container_nginx.

### 3.8 New script and Make target

- `scripts/restore_prod_to_preview.sh` — reads `DATABASE_URL_RO` from prod project + `DATABASE_URL` from preview project (Scaleway Secret Manager), runs `pg_dump | drop schema | pg_restore`. Requires `SCW_PROD_PROJECT_ID` and `SCW_PREVIEW_PROJECT_ID` env vars.
- `Makefile` — added `db-restore-preview-from-prod` target wrapping the script.

### 3.9 New GitHub Actions workflow

`.github/workflows/_webapp-build-and-push-docker.yml` — mirrors `_airflow-build-and-push-docker.yml`. Builds `webapp` and `webapp-nginx` images in one job, pushes to `rg.fr-par.scw.cloud/ns-qfdmo/`. Triggered manually via `workflow_dispatch` with `image_tag` and `environment` inputs.

### 3.10 Documentation

`docs/reference/infrastructure/provisioning.md` — appended a full "Preview environment" section: image build, secret bootstrap (with bare names + per-project isolation explained), Scaleway API creds, Airflow `TF_VAR_*` env vars, `terragrunt run-all apply` order, DB seed step, optional second-phase `BASE_URL` apply, and secret rotation snippet.

## 4. Outstanding (NOT done yet)

These came out of a code-reviewer agent pass at the end of the session. Three were fixed; **three remain open and matter**.

### 4.1 BLOCKER — `restore_prod_to_preview.sh` `scw` CLI verification

I rewrote the script to use `scw secret secret access-by-name name=… project-id=… revision=latest_enabled -o json` based on what I believe to be the current CLI form, **but I have not verified this on a live machine**. The Scaleway CLI evolves, and the original review caught me using a wrong `access-by-path` form. Action: run `scw secret -h` and `scw secret secret -h` on the operator's machine and confirm the subcommand chain. If wrong, the most likely correct form is one of:

- `scw secret secret-version access-by-name secret-name=<name> project-id=<id> revision=latest_enabled -o json`
- `scw secret secret access-by-name name=<name> project-id=<id> revision=latest_enabled -o json` (what I used)

The `data` field in the JSON response is base64-encoded — the script's Python one-liner decodes it. Verify that too.

### 4.2 NON-BLOCKING — `proxy_ssl_name` unix-socket guard

In `servers.conf.erb`, if someone misconfigures `UPSTREAM_HOST=unix:/tmp/gunicorn.sock` with `UPSTREAM_SCHEME=https`, `upstream_sni` becomes `unix:/tmp/gunicorn.sock` and nginx will fail SNI. Add a guard:

```erb
<% raise "UPSTREAM_SCHEME=https requires a non-unix UPSTREAM_HOST" if upstream_scheme == "https" && upstream_host.start_with?("unix:") %>
```

### 4.3 NON-BLOCKING — Workflow `concurrency:` group

Two simultaneous deploys can race-push the same tag. Add to `_webapp-build-and-push-docker.yml`:

```yaml
concurrency:
  group: webapp-build-${{ inputs.environment }}-${{ inputs.image_tag }}
  cancel-in-progress: false
```

### 4.4 NON-BLOCKING — Healthcheck on a dedicated path

The webapp + nginx healthchecks currently hit `/`. Django's home view returns 200 unauthenticated, but it depends on `ALLOWED_HOSTS` accepting the healthcheck origin and on Wagtail rendering a real page. A dedicated `/health/` endpoint in Django would be more durable. Out of scope for this session; track separately.

### 4.5 NOT CHECKED — `tofu validate` / `terragrunt plan`

I did NOT run `tofu validate` or `terragrunt plan` against any of the new files. The first invocation will likely surface things I missed. Run from `infrastructure/environments/preview/`:

```sh
terragrunt run-all init
terragrunt run-all validate
terragrunt run-all plan
```

Expect at minimum these surfaces of breakage:

- The `data.scaleway_secret` resource may reject lookups on non-existent secrets — operator must `scw secret secret create` for all 11 webapp secret names BEFORE running plan.
- The `dependency` mock_outputs only allow `validate` and `plan`; if you `apply` directly without going through `run-all`, you may hit "dependency not yet applied" errors — that's expected, not a bug.

## 5. How to take this forward

If the next person is going to **apply** this for the first time:

1. Read `docs/reference/infrastructure/provisioning.md` end-to-end (the new "Preview environment" section).
2. Verify the `scw` CLI command in `scripts/restore_prod_to_preview.sh` (item 4.1 above).
3. Trigger the GitHub workflow once to publish `webapp:preview` and `webapp-nginx:preview` to the registry.
4. Create all 11 secrets via `scw secret secret create name=<bare-name>` in the preview project (a279f7ac-06ce-4236-9d78-51298d8d72ed), then add a version with `scw secret version create secret-id=<id> data=-` for each.
5. Set `TF_VAR_access_key` and `TF_VAR_secret_key` from a password manager.
6. Set the airflow-only `TF_VAR_*` env vars (the ones not yet migrated to Secret Manager — see `preview/container/terragrunt.hcl` for the full list, all use `get_env("TF_VAR_…", "")`).
7. `cd infrastructure/environments/preview && terragrunt run-all init && terragrunt run-all plan`.
8. If plan looks sane, `terragrunt run-all apply`.
9. After nginx is up, run `make db-restore-preview-from-prod` (with both `SCW_*_PROJECT_ID` env vars set).
10. Optional: set `TF_VAR_PREVIEW_BASE_URL` to the actual nginx URL and re-apply `container_webapp`.

If the next person is going to **iterate** without applying:

- Run `tofu validate` and `terragrunt plan` first (item 4.5) and pin down the actual surface of issues before reasoning about fixes.
- Don't change `modules/container/` signatures further without verifying preprod/prod stay no-op-on-plan. The current additive shape is the result of a deliberate roll-back from a more aggressive refactor.

## 6. Files touched (full list)

### New

- `infrastructure/modules/container/outputs.tf`
- `infrastructure/modules/container/secrets.tf`
- `infrastructure/modules/object_storage/webapp.tf`
- `infrastructure/modules/object_storage/outputs.tf`
- `infrastructure/modules/container_webapp/{main,variables,outputs,secrets}.tf`
- `infrastructure/modules/container_nginx/{main,variables,outputs}.tf`
- `infrastructure/environments/preview/object_storage/terragrunt.hcl`
- `infrastructure/environments/preview/container/terragrunt.hcl`
- `infrastructure/environments/preview/container_webapp/terragrunt.hcl`
- `infrastructure/environments/preview/container_nginx/terragrunt.hcl`
- `scripts/restore_prod_to_preview.sh`
- `.github/workflows/_webapp-build-and-push-docker.yml`
- `SESSION_HANDOFF_preview_environment.md` (this file)

### Modified

- `infrastructure/environments/root.hcl`
- `infrastructure/environments/variables.tf`
- `infrastructure/environments/preview/database/terraform.tfvars.example`
- `infrastructure/modules/container/variables.tf`
- `infrastructure/modules/container/airflow-scheduler.tf`
- `infrastructure/modules/object_storage/variables.tf`
- `webapp/servers.conf.erb`
- `Makefile`
- `docs/reference/infrastructure/provisioning.md`

### Untouched but referenced

- `webapp/Dockerfile`, `webapp/nginx/Dockerfile`, `webapp/nginx/entrypoint.sh` — consumed by the new image build workflow; no edits needed.
- `infrastructure/modules/container/airflow-webserver.tf` — intentionally NOT extended (DAGs run on the scheduler, not the webserver).
- `infrastructure/modules/database/`, `database_sample/`, `container_registry/` — untouched.

## 7. Quirks worth knowing

- **Webapp ↔ nginx is NOT a circular Terragrunt dependency.** Only nginx depends on webapp's `domain_name`. Webapp's `BASE_URL` is empty by design; the operator sets it via `TF_VAR_PREVIEW_BASE_URL` and re-applies `container_webapp` once nginx is up. Don't try to "fix" this with a bidirectional dependency — it will deadlock the dependency graph.
- **The preview env directory imposes airflow on the apply graph.** webapp and nginx both depend on `container/` because that's where the namespace is created. If you ever need a webapp-only preview, extract the namespace into its own module — but be prepared for the preprod/prod state migration cost (see item 2 in "Decisions" / the rolled-back attempt at `modules/container_namespace/`).
- **`scaleway_container.domain_name`** returns the random-UUID Scaleway URL like `<uuid>.functions.fnc.fr-par.scw.cloud`. To get a stable hostname, add a `scaleway_container_domain` resource with a CNAME you control — out of scope here.
- **When `use_secret_manager = true` on the airflow module, the secrets MUST exist in the project before the first plan**, otherwise `data.scaleway_secret` errors out. Bootstrap secrets first, plan second.
- **Bare secret names in scripts** require setting `SCW_PROD_PROJECT_ID` and `SCW_PREVIEW_PROJECT_ID` env vars — they tell the script which project to look in. Without them, `scw` falls back to your default profile project, which would mix envs.

---

**End of handoff.** If anything here is wrong or unclear, the session log is in the conversation history of the branch `deploy_to_scaleway` — git blame the files above to find the relevant exchanges.
