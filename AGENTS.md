# AGENT Guidelines - Monorepo Guide

> **Purpose**: Context for AI assistants and developers. For app-specific patterns, see individual README.md files and `docs/`.

## Main monorepo architecture

| Path                         | Purpose                                                    | Technologies                                                                |
| ---------------------------- | ---------------------------------------------------------- | --------------------------------------------------------------------------- |
| `.github/`                   | CI/CD                                                      | GitHub Actions                                                              |
| `webapp/`                    | Django + Stimulus app “Que faire de mes objets et déchets” | Django, Wagtail, TypeScript, Stimulus, Parcel, Tailwind, pytest, Playwright |
| `data-platform/`             | Data platform (Airflow, dbt, notebooks)                    | Airflow, dbt, Python, pytest                                                |
| `docs/`                      | Technical documentation                                    | Sphinx, Markdown                                                            |
| `infrastructure/`            | Infrastructure deployment and management                   | OpenTofu, Terragrunt, Scaleway                                              |
| `docker-compose.yml`         | Local stack: webapp, worker, assets, nginx, DBs, Airflow   | Docker Compose (`airflow` profile)                                          |
| `webapp/nginx/`              | Local nginx (HTTP on `.localhost`)                         | nginx                                                                       |
| `Makefile`                   | Root command aliases (delegates to subprojects)            | Make                                                                        |
| `scripts/`                   | Scripts outside the webapp (DB restore, backups)           | bash, SQL                                                                   |
| `pyproject.toml` / `uv.lock` | uv workspace (Python 3.12)                                 | uv                                                                          |

**Python:** uv workspace at the repo root (`members = ["webapp", "data-platform"]`), single `uv.lock`. The root project depends only on the webapp member (Scalingo build). `uv sync` alone does **not** install data-platform.

**Local stack:** Docker only, see [docs/how-to/development/installation.md](./docs/how-to/development/installation.md). Node, Python and uv versions come from `.tool-versions`.

```sh
make setup   # build the images, start the stack, migrate, populate an empty DB
make up      # after a git pull
```

On the host (pre-commit hooks, editor), webapp-only: `uv sync --group dev --group webapp-dev`. Data-platform tests (as in CI): `uv sync --all-packages --group dev`. Targeting a member with `cd webapp && uv sync` / `cd data-platform && uv sync` also works, but still needs the relevant `--group` flags for pytest/ruff.

**JavaScript:** npm workspace (`webapp/` is the only workspace). Node 24, `npm ci` runs in the `assets` container.

Project-specific Make targets live in `webapp/Makefile` and `data-platform/Makefile`. The root `Makefile` exposes prefixed aliases (`webapp-unit-test`, `data-platform-dags-test`, …). Unprefixed targets (`unit-test`, `dags-test`) only exist inside those directories.

## Common commands

| Task                                             | Directory               | Command                             |
| ------------------------------------------------ | ----------------------- | ----------------------------------- |
| Whole local stack                                | repo root               | `make setup` / `make up`            |
| Django + `db_worker` + Parcel watch              | `webapp/`               | `make runserver`                    |
| Airflow stack                                    | repo root               | `make run-airflow`                  |
| Format (Black + Ruff; SqlFluff in data-platform) | repo root or subproject | `make format` / `make check-format` |
| Webapp unit tests                                | `webapp/`               | `make unit-test`                    |
| Webapp integration tests                         | `webapp/`               | `make integration-test`             |
| Webapp JS tests (Jest)                           | `webapp/`               | `make js-test`                      |
| Webapp e2e (Playwright)                          | `webapp/`               | `make e2e-test`                     |
| DAG tests                                        | `data-platform/`        | `make dags-test`                    |
| TypeScript lint / Prettier                       | `webapp/`               | `npm run lint` / `npm run format`   |

Equivalent from repo root: `make webapp-unit-test`, `make webapp-integration-test`, `make webapp-e2e-test`, `make webapp-js-test`, `make data-platform-dags-test`.

Django management commands run in the containers: `make migrate`, `make shell`, … from `webapp/`.

## Using English or French

Use English in code and technical markdown. Details: [docs/reference/coding/README.md](./docs/reference/coding/README.md).

## Quick Lookup

| Topic                                    | Go to…                                                                                           |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Local install                            | [docs/how-to/development/installation.md](./docs/how-to/development/installation.md)             |
| Python / npm dependencies                | [docs/how-to/development/dependencies.md](./docs/how-to/development/dependencies.md)             |
| API features                             | [docs/reference/apis/README.md](./docs/reference/apis/README.md)                                 |
| Webapp (Django / JS)                     | [docs/reference/webapp/README.md](./docs/reference/webapp/README.md)                             |
| Django apps and async tasks              | [docs/reference/webapp/django.md](./docs/reference/webapp/django.md)                             |
| Templating                               | [docs/reference/webapp/templates.md](./docs/reference/webapp/templates.md)                       |
| Look and feel (DSFR / Tailwind)          | [docs/reference/webapp/look-and-feel.md](./docs/reference/webapp/look-and-feel.md)               |
| Javascript (Stimulus / Maplibre / Turbo) | [docs/reference/webapp/javascript.md](./docs/reference/webapp/javascript.md)                     |
| A/B testing (PostHog)                    | [docs/reference/webapp/ab-testing.md](./docs/reference/webapp/ab-testing.md)                     |
| Internationalization                     | [docs/reference/webapp/internationalization.md](./docs/reference/webapp/internationalization.md) |
| Architecture                             | [docs/reference/architecture/README.md](./docs/reference/architecture/README.md)                 |
| Database                                 | [docs/reference/db/README.md](./docs/reference/db/README.md)                                     |
| Infrastructure                           | [docs/reference/infrastructure/provisioning.md](./docs/reference/infrastructure/provisioning.md) |
| Monitoring                               | [docs/reference/infrastructure/monitoring.md](./docs/reference/infrastructure/monitoring.md)     |
| CI/CD                                    | [docs/reference/infrastructure/ci-cd.md](./docs/reference/infrastructure/ci-cd.md)               |
| Security                                 | [docs/reference/security/README.md](./docs/reference/security/README.md)                         |
| Airflow                                  | [docs/reference/data-platform/airflow.md](./docs/reference/data-platform/airflow.md)             |
| DBT                                      | [docs/reference/data-platform/dbt.md](./docs/reference/data-platform/dbt.md)                     |
| Open data                                | [docs/reference/opendata/README.md](./docs/reference/opendata/README.md)                         |

## Project structure

```txt
/
├── .github/                 # CI/CD workflows
├── webapp/                  # Django + Stimulus « Que faire de mes objets et déchets »
│   ├── settings/            # Django settings (base, dev, test, airflow)
│   ├── core/                # URLs, WSGI, shared utilities / templatetags
│   ├── qfdmo/               # Map and acteurs
│   ├── qfdmd/               # Wagtail CMS and tri advice
│   ├── search/              # Search
│   ├── data/                # Backoffice data / suggestions
│   ├── infotri/             # Infotri widget
│   ├── stats/               # Stats API
│   ├── nginx/               # Local nginx
│   ├── static/
│   │   ├── to_compile/      # TypeScript / CSS sources (Parcel)
│   │   ├── to_collect/      # Extra static assets
│   │   └── compiled/        # Parcel output
│   ├── templates/           # Django templates
│   ├── unit_tests/
│   ├── integration_tests/
│   └── e2e_tests/           # Playwright
├── data-platform/
│   ├── dags/                # Airflow DAGs (tests in dags/tests/)
│   ├── dbt/                 # dbt models
│   ├── notebooks/
│   ├── config/              # Airflow config
│   └── plugins/
├── docs/                    # Sphinx technical documentation
├── infrastructure/          # OpenTofu / Terragrunt
├── docker-compose.yml
├── Makefile                 # Root aliases
├── pyproject.toml           # uv workspace root
├── uv.lock
└── scripts/                 # DB restore, backups, SQL
```

## Code conventions

### Python

- **Lint:** Ruff (`webapp/pyproject.toml` and `data-platform/pyproject.toml`)
- **Format:** Black, line-length 88
- Type hints when relevant
- Imports: Organized according to Django conventions (stdlib, third-party, local). Import the symbols you use directly (`from package.module import func`), not the module for qualified access (`import module` then `module.func`).
- Tests: pytest; webapp uses pytest-django (`settings.test`)
- Language rules: [docs/reference/coding/README.md](./docs/reference/coding/README.md)

### TypeScript

- Conventions: [TypeScript style guide](https://ts.dev/style/)
- Enforced in CI by eslint / prettier (`webapp/`)

## Documentation

- Technical documentation is in `docs/` and published on GitHub Pages
- Start from [docs/how-to/development/installation.md](./docs/how-to/development/installation.md) for local setup
- Specific READMEs live in important subfolders
