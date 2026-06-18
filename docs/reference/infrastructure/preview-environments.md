# Preview environments

Ephemeral, per-PR deployments of the webapp on Scaleway, provisioned with
OpenTofu/Terragrunt from CI.

## How to use

1. Add the `preview` label to a pull request.
2. `preview-up.yml` builds the webapp Docker image, applies the terragrunt
   stack and posts a sticky comment on the PR with the environment URL.
3. Every push to the PR rebuilds the image and redeploys the same
   environment (same URL).
4. The environment is destroyed when the PR is closed or the `preview`
   label is removed. A nightly cron also reaps any preview older than
   7 days as a safety net.

## Decisions

| Topic               | Decision                               | Rationale                                                                                                                                                               |
| ------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Env keying          | **PR number** (`pr-<n>`)               | Stable URL across pushes, one env per PR, destroyed on close.                                                                                                           |
| Trigger             | **Label-gated** (`preview` label)      | Each up run builds a Docker image and seeds a DB: real cost, several minutes. Labeling opts a PR in.                                                                    |
| Hostname            | **Scaleway generated domain**          | No DNS to manage. The hostname is unknown before apply, so the container runs with `ALLOWED_HOSTS` relaxed to `.functions.fnc.fr-par.scw.cloud`.                        |
| Container namespace | **Dedicated `lvao-preview` namespace** | Isolation from preprod; the cleanup cron can list it exhaustively.                                                                                                      |
| DB seeding          | **`pg_dump` sample DB → `pg_restore`** | Realistic data on the carte from the preprod sample database.                                                                                                           |
| Cleanup TTL         | **7 days** (nightly cron)              | With PR keying + destroy-on-close the cron is only a safety net for missed destroys. A shorter TTL would kill envs of still-open PRs and dead URLs in their PR comment. |

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
│                   1-day object expiry; container reuses the
│                   project-wide SCW key (no bucket-scoped IAM key,
│                   see Limitations)
└── container       serverless container in the shared
                    lvao-preview namespace, min_scale=0,
                    tagged preview / preview-pr-<n> /
                    created-at-<unix>

Shared (one-time):
└── lvao-preview container namespace
    (infrastructure/environments/preview/namespace)
```

The image tag embeds the PR head SHA (`pr-<n>-<shortsha>`) so each push
changes the container's `registry_image`, which is what forces Scaleway to
redeploy.

State keys and the `environment` terragrunt input (`pr-<n>`) derive from
the materialised directory path through `root.hcl` — the per-PR stacks
carry no backend overrides.

Teardown paths, all converging on `terragrunt run-all destroy` plus state
object deletion:

1. PR closed or `preview` label removed → `preview-down.yml`
2. Nightly cron (`preview-cleanup.yml`) dispatches `preview-down.yml` for
   anything whose `created-at-<unix>` tag is older than 7 days
3. Manual `workflow_dispatch` of `preview-down.yml` with a PR number

Old `pr-*` image tags are reaped by the existing weekly
`scaleway_container_registry_delete_old_tags.yml` job (keeps the 30 most
recent tags per image).

## Bootstrap (one-time setup)

Everything is automated by `infrastructure/Makefile`. With the Scaleway
credentials exported in your shell (or in the repo root `.env`):

```bash
export SCW_ACCESS_KEY=…              # able to manage RDB databases/users,
export SCW_SECRET_KEY=…              # object storage, IAM and containers
export SCW_DEFAULT_PROJECT_ID=…
export SCW_DEFAULT_ORGANIZATION_ID=…
export SCALEWAY_DOCKER_SECRET=…      # registry push credential
export SAMPLE_DB_URI=…               # postgres URI of the preprod sample DB
                                     # (pg_dump source), reachable from CI

make -C infrastructure preview-bootstrap
```

This runs three idempotent steps, also callable individually:

1. `preview-github-env` — creates the GitHub `preview` environment and
   pushes the secrets above, plus `PREVIEW_SECRET_KEY` (the shared Django
   `SECRET_KEY` for previews, generated with `openssl rand` unless already
   set in your shell).
2. `preview-namespace` — `terragrunt apply` of the shared `lvao-preview`
   container namespace (interactive: review the plan before approving).
3. `preview-label` — creates the `preview` label on the repository.

## Validation checklist

On a test PR:

- [ ] Labeling creates the env; the sticky comment links a working URL
- [ ] Migrations ran, sample data visible on the carte, `/healthz` green
- [ ] A second push updates the same env, same URL
- [ ] Removing the label (or closing the PR) destroys all three stacks
- [ ] State objects gone from `lvao-terraform-state/preview/pr-<n>/`
- [ ] Cron dry-run (`preview-cleanup.yml` with `dry_run=true`) lists an
      artificially aged container as stale

## Limitations / out of scope

- Webapp only: no Airflow/data-platform previews, no warehouse database
  (the entrypoint skips `create_remote_db_server` when `DB_WAREHOUSE` is
  unset).
- Production deployment is unchanged (Scalingo); the Docker image is
  used by previews only for now.
- Served on the Scaleway-generated domain; no custom URLs.
- No bucket-scoped IAM key for the media bucket: the CI Terraform credentials
  (`SCW_ACCESS_KEY`/`SCW_SECRET_KEY`) lack IAM write permission, so the
  container reuses those project-wide credentials for S3 access instead of a
  bucket-scoped key. Any preview container can therefore reach every bucket
  in the project, not just its own. Revisit once IAM write access is granted
  (see TODO below) — re-add `scaleway_iam_application` /
  `scaleway_iam_policy` / `scaleway_iam_api_key` in `preview_object_storage`,
  scoped to the bucket.

## TODO

- **Separate Scaleway project for previews**: currently all preview resources
  (containers, databases, buckets) are created in the same Scaleway
  project as preprod. A dedicated preview project would provide billing
  isolation and quota isolation. To implement: create a `preview` Scaleway
  project, add `SCW_PREVIEW_PROJECT_ID` as a GitHub secret in the `preview`
  environment, and update `_terragrunt-apply.yml` to pass it as
  `TF_VAR_project_id`.
- **Grant IAM write permission to the CI Scaleway key**: needed to restore
  bucket-scoped IAM credentials per preview (see Limitations above). Without
  it, the IAM isolation between previews and prod/preprod buckets is weaker
  than intended.
