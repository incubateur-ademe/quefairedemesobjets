# CI/CD Documentation

This documentation describes the different CI/CD workflows of the project and what happens in each use case.

## Python / uv in CI

Python jobs use a **single workspace virtual environment** at the repo root, synced with semantic dependency groups:

- **`--group lint`**: Black + Ruff for CI linter.
- **`--group dev`**: lint + test (pytest, factory-boy) + djade + pre-commit for CI tests / checks.
- **`--group dev --group webapp-dev`**: Full local dev (adds Django runserver tooling, debug toolbar, etc.).

`uv sync` always runs from the repo root (the workspace root). The reusable job [`.github/workflows/_pytest-job.yml`](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/.github/workflows/_pytest-job.yml) syncs `--group dev` from root, then runs `make -C <webapp|data-platform> <target>`.

## Creating or updating a Pull Request

When a Pull Request is created, updated or marked as ready for review (events `opened`, `synchronize`, `ready_for_review` or `converted_to_draft`), the **💣 Pull request** workflow ([review.yml](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/.github/workflows/review.yml)) is triggered.

One reusable workflow runs per app: **🌐 Webapp** ([ci-webapp.yml](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/.github/workflows/ci-webapp.yml)), **📊 Data platform** ([ci-data-platform.yml](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/.github/workflows/ci-data-platform.yml)), **🧐 Revue** ([ci-revue.yml](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/.github/workflows/ci-revue.yml)) and **🏗️ Infrastructure** ([ci-infrastructure.yml](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/.github/workflows/ci-infrastructure.yml)). They run in parallel and always to the end, so a pull request shows all its failures at once, and `✅ CI` fails if one of them fails.

A Pull Request does not deploy to `preprod`. The optional preview ([preview-up.yml](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/.github/workflows/preview-up.yml)) is triggered by the `preview` label. It is a separate workflow: it does not wait for CI, and a CI failure does not stop it.

Draft pull requests run no CI or E2E: they start when the pull request is marked as ready for review, and converting a pull request to draft cancels what is running.

In a [stack of pull requests](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/optimizing-ci-for-stacked-pull-requests), only the top pull request runs CI and E2E, as it contains the changes of the whole stack. Lower pull requests report the required checks as skipped so they stay mergeable, which means a lower pull request can merge even if the top one fails: check the top pull request before merging.

The `🔎 Scope` job reads this from the API rather than from the event, as it is more recent than the payload. `gh stack submit` opens each pull request before linking the stack and no workflow event follows, so a pull request opened as ready for review usually does not know its stack yet and runs CI once.

To avoid this, open a stack as drafts, then mark its pull requests as ready: `gh stack submit --auto` creates drafts by default, unlike `--open` or the interactive editor. A push made before linking new pull requests into a stack has the same effect on the pull request that was the top one.

When the top pull request is closed without merging, the new top keeps its skipped checks until its next push.

On a Pull Request, only the apps matching the changed files run, the others being skipped by `review.yml`: [ci-areas.yml](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/.github/ci-areas.yml) maps files to areas for `dorny/paths-filter`, and an unrecognised file runs everything. In a stack, files are compared with the stack base, so the top pull request covers the whole stack. A webapp change also runs the data platform jobs, as the DAGs import the webapp, but not the other way round. `ml_deduplication` runs no CI job. Everything runs on `main`.

The required check is `✅ CI`: it fails if a CI job failed or was cancelled, and passes if they were skipped. Requiring the jobs themselves would let a pull request merge with a failed linter, as a skipped job counts as passed.

Python tests run on 4 pytest-xdist workers, against PostgreSQL in memory. Migrations are the slowest part of a test run and each worker would replay them, so [prepare-test-databases](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/.github/actions/prepare-test-databases/action.yml) restores a dump cached on `uv.lock` and the migrations, then clones it per worker. A pull request that changes either migrates once per job, until `main` has saved the new dump.

### Review workflow flow

```mermaid
graph TD
    A[Pull request] --> B[Scope<br/>draft, stack, changed areas]
    B --> C[Webapp]
    B --> D[Data platform]
    B --> F[Revue]
    B --> H[Infrastructure]
    B --> E[E2E<br/>with the frontend label<br/>or a change in .github]
    C --> G[CI, the required check]
    D --> G
    F --> G
    H --> G
```

## Merging a PR into main

When a Pull Request is merged into the `main` branch, the **🌚 Main to preprod** workflow ([cd.yml](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/.github/workflows/cd.yml)) is triggered.

Deployment to `preprod` does not wait for CI, and a CI failure does not stop it. CI runs in parallel, as on a pull request. The draft release is only updated when CI and both deployments succeeded.

A new commit on `main` cancels the run in progress, so only the last commit gets deployed.

### CD workflow flow

```mermaid
graph TD
    A[Push on main] --> C[CI of each app]
    A --> W{Confirm deployment to preprod?}
    W -->|Yes| F[Webapp deployment]
    W -->|Yes| G[Build Airflow images and deploy on Scaleway]
    A --> E[E2E tests]
    C --> H[Update of the draft release]
    F --> H
    G --> H
```

## Publishing a release

When a release is published on GitHub (event `published`), the **🌞 Release to production** workflow ([deploy.yml](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/.github/workflows/deploy.yml)) is triggered to deploy to production.

The tagged version of the code is deployed to the `prod` environment.

### Deploy workflow flow

```mermaid
graph TD
    C[Deployment of the webapp release version to production]
    F[Build Airflow Docker images<br/>The image is tagged with the version number<br/>This tagged image is used for the production deployment]
    F --> H[Deployment of the Scheduler on Scaleway in production]
    F --> I[Deployment of the Webserver on Scaleway in production]
```

## Scheduled workflows

### Database synchronization

The `sync_databases.yml` workflow synchronizes production data to preproduction.

**Schedule**: Every Sunday at midnight (cron: `0 0 * * SUN`)

**Actions performed**:

- Restore the production database to preproduction
- Run migrations in a one-off container
- Reset the suggestions table
- Create the remote database server between webapp and warehouse
- Synchronize S3 buckets (copy from prod to preprod)

### Dependabot

The `dependabot.yml` file configures automatic dependency updates.

**Schedule**: Every Tuesday at 06:00 UTC

**Ecosystems monitored**:

- **uv**: Python dependencies (weekly)
- **npm**: JavaScript dependencies (weekly, grouped by categories: parcel, jest, eslint)
- **GitHub Actions**: Actions used in the workflows (weekly)
- **Terraform**: Terraform modules in `/infrastructure` (weekly)

### Documentation publication

The `publish-docs.yml` workflow automatically publishes the documentation to GitHub Pages.

**Trigger**: On every push to the `main` branch

The documentation is available here: https://incubateur-ademe.github.io/quefairedemesobjets/README.html

## Environments

The project uses several GitHub environments to store environment variables specific to each of them: **preprod** and **prod**.

## Notifications

Production deployments trigger Mattermost notifications in the `lvao-tour-de-controle` channel:

- Deployment start notification
- Success notification with URL
- Failure notification with a link to the logs
- Notification if the site is down after deployment
