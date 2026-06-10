# Preview environments (plan)

Ephemeral, per-PR deployments of the webapp on Scaleway, provisioned with
OpenTofu/Terragrunt from CI. This document is the implementation plan; it
will be reworked into regular reference documentation once the feature
ships.

## Prior art

- **`origin/preview-env-iac`** — a complete first implementation, keyed by
  commit SHA, concentrated in commit `a8179449a`. The branch has drifted
  far from `main` (it also carries a Scalingo→Scaleway migration), so the
  preview work is extracted from it rather than merged.
- **[plusfraisautravail](https://github.com/incubateur-ademe/plusfraisautravail)**
  — reference for running terraform in CI: `tofu plan` on PRs touching
  `infra/**`, apply on main with the plan in the job summary, concurrency
  groups serializing applies, image rollouts decoupled from terraform,
  secrets scoped via GitHub environments.

## Decisions

| Topic               | Decision                                           | Rationale                                                                                                                                                                                                                                                        |
| ------------------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Env keying          | **PR number** (`pr-<n>`)                           | Stable URL across pushes, one env per PR, destroyed on close. The prior art's SHA keying creates a new env per push and relies on the TTL cron to reap orphans.                                                                                                  |
| Trigger             | **Label-gated** (`preview` label)                  | Each up run builds a Docker image and seeds a DB: real cost, several minutes. Labeling opts a PR in; pushes update the env in place; unlabeling or closing destroys it.                                                                                          |
| Hostname            | **Scaleway generated domain**                      | No DNS to manage. The hostname is unknown before apply, so the preview container runs with `ALLOWED_HOSTS` relaxed to `.functions.fnc.fr-par.scw.cloud`. Acceptable for throwaway envs; revisit with a wildcard domain if clean URLs become worth the DNS setup. |
| Container namespace | **Dedicated `lvao-preview` namespace**             | Isolation from preprod; the cleanup cron can list it exhaustively. The prior art reused the preprod namespace via env var.                                                                                                                                       |
| DB seeding          | **`pg_dump` sample DB → `pg_restore`** (prior art) | Realistic data on the carte from the preprod sample database. Runner needs network access to both DBs.                                                                                                                                                           |
| Cleanup TTL         | **7 days** (nightly cron)                          | With PR keying + destroy-on-close the cron is only a safety net for missed destroys. 24h (prior art) would kill envs of still-open PRs overnight.                                                                                                                |
| Delivery            | **Single branch**                                  | One clean branch off `main`, essentially a tidied `preview-env-iac`, reviewed as one PR.                                                                                                                                                                         |

## Architecture

```
PR #123 labeled "preview"
        │
        ▼
┌─ preview-up.yml ─────────────────────────────────────────────┐
│ 1. build webapp image  → rg.fr-par.scw.cloud/ns-qfdmo/       │
│                          webapp:pr-123-<shortsha>            │
│ 2. terragrunt run-all apply                                  │
│      infrastructure/environments/preview/pr-123/             │
│      (materialised from _template at runtime)                │
│ 3. sticky PR comment with the URL                            │
└──────────────────────────────────────────────────────────────┘

Per-PR resources (state: lvao-terraform-state/preview/pr-<n>/…):
├── database        DB + user + privilege on the EXISTING preprod
│                   RDB instance, PostGIS extensions, seeded from
│                   the sample DB
├── object_storage  throwaway media bucket, force_destroy,
│                   1-day object expiry, bucket-scoped IAM key
└── container       serverless container in the shared
                    lvao-preview namespace, min_scale=0,
                    tagged preview / preview-pr-<n> /
                    created-at-<unix>

Shared (one-time):
└── lvao-preview container namespace
```

Teardown paths, all converging on `terragrunt run-all destroy`:

1. PR closed or `preview` label removed → `preview-down.yml`
2. Nightly cron (`preview-cleanup.yml`) reaps anything whose
   `created-at-<unix>` tag is older than 7 days, via
   `repository_dispatch`
3. Manual `workflow_dispatch` with a PR number

## Work breakdown

All on one branch, in commit-reviewable steps.

### 1. Containerize the webapp

Ported from `a8179449a`, FIXMEs resolved:

- `webapp/Dockerfile` — multi-stage: Node/parcel asset build, then
  Python 3.12 + GDAL runtime with `uv sync --frozen --no-dev`,
  `compilemessages`, `collectstatic`. Built for `linux/amd64` only
  (Scaleway serverless containers are amd64; the prior art missed this).
- `webapp/bin/entrypoint.sh` — createcachetable, migrate, enable
  unaccent/trigram, clearsessions, clear_cache, gunicorn.
- `webapp/.dockerignore`
- `/healthz` endpoint (does not exist on `main`; the container health
  check targets it).
- `.github/workflows/_webapp-build-and-push-docker.yml` — reusable
  workflow, GHA layer cache, pushes to `ns-qfdmo`.

### 2. Terraform-in-CI plumbing

- `.github/workflows/_terragrunt-apply.yml` — reusable: installs
  OpenTofu + Terragrunt + postgresql-client, materialises
  `environments/preview/_template` → `environments/preview/pr-<n>`,
  runs `run-all <apply|destroy>`. Plan output goes to
  `$GITHUB_STEP_SUMMARY`; concurrency handled by the callers.
- Remove the stale `infrastructure/environments/preview/{database,…}`
  stacks from `main` (an old copy of the full `database` module that
  would provision dedicated RDB instances — unrelated to per-PR
  previews).

### 3. Preview modules

Ported from the prior art, re-keyed `COMMIT_SHA` → `PR_NUMBER`:

- `modules/preview_database` — `scaleway_rdb_database` + user +
  privilege on the preprod instance, `null_resource` provisioners for
  `create_extensions.sql` and the `pg_dump | pg_restore` seed.
- `modules/preview_object_storage` — bucket with `force_destroy`,
  1-day lifecycle expiry, bucket-scoped IAM application/policy/api-key.
- `modules/webapp_container` — container + `time_static.created_at`
  tag for the TTL cron. No custom-domain resource (generated domain).
- `environments/preview/_template/{database,object_storage,container}`
  — terragrunt stacks wired with `dependency` blocks, isolated state
  keys `preview/pr-<n>/<component>/terraform.tfstate`.

### 4. Lifecycle workflows

- `preview-up.yml` — on `pull_request` `labeled`/`synchronize` (gated
  on the `preview` label) + `workflow_dispatch`. Build → apply →
  sticky comment (one comment updated in place). Concurrency group
  `preview-pr-<n>`, `cancel-in-progress: false`.
- `preview-down.yml` — on `unlabeled`/`closed` + `workflow_dispatch` +
  `repository_dispatch(preview-cleanup)`. Destroy, then delete the
  state objects and the `pr-<n>-*` registry tags.
- `preview-cleanup.yml` — nightly cron, `scw container container list
tags.0=preview`, reads `created-at-<unix>`, dispatches destroys past
  the 7-day TTL. `dry_run` and `ttl_hours` inputs for manual runs.

### 5. Bootstrap & validation

One-time setup:

- GitHub `preview` environment with `SCW_*` credentials,
  `PREVIEW_SECRET_KEY`, `SAMPLE_DB_URI`, and the preview namespace ID.
- Create the `lvao-preview` container namespace (terragrunt, applied
  once).
- Create the `preview` label.

Validation checklist on a test PR:

- [ ] Labeling creates the env; the sticky comment links a working URL
- [ ] Migrations ran, sample data visible on the carte, `/healthz` green
- [ ] A second push updates the same env, same URL
- [ ] Removing the label (or closing the PR) destroys all three stacks
- [ ] State objects gone from `lvao-terraform-state/preview/pr-<n>/`
- [ ] Cron dry-run lists an artificially aged container as stale

## Out of scope

- Airflow / data-platform previews — webapp only.
- Production deployment changes — prod stays on Scalingo; the Docker
  image is used by previews only for now.
- CDN/TLS-fronted custom URLs.
