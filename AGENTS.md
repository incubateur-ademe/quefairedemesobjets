# AGENT Guidelines - Monorepo Guide

> **Purpose**: Context for AI assistants and developers. For app-specific patterns, see individual README.md files.

## Main monorepo architecture

| Repository or file   | Purpose                                                      | Technologies                                               |
| -------------------- | ------------------------------------------------------------ | ---------------------------------------------------------- |
| `.github/`           | CI/CD                                                        | Github action                                              |
| `webapp/`            | Django + Stimulus app “What to do with my objects and waste” | Django, Typescript, Stimulus, pytest, playwright, tailwind |
| `data-platform/`     | Data platform (Airflow, dbt, notebooks…)                     | Airflow, dbt, python, pytest                               |
| `docs/`              | Technical documentation                                      | sphinx, markdown                                           |
| `infrastructure/`    | Infrastructure deployment and management                     | opentofu, terragrunt, Scaleway                             |
| `docker-compose.yml` | Local execution                                              | docker, docker compose                                     |
| `nginx-local-only/`  | Nginx config for local development                           | nginx                                                      |
| `Makefile`           | Global commands                                              |                                                            |
| `scripts/`           | Scripts outside webapp                                       | bash                                                       |
| `pyproject.toml`     | Python dependencies (uv)                                     |                                                            |

Note : `webapp/Makefile` handle `webapp` specific command

## Using English or French

Use English by default, for more guidelines : [docs/reference/coding/README.md](./docs/reference/coding/README.md)

## Quick Lookup

For each kind of task below, refer to the specific documentation

| Is concerned                               | Go to...                                                                                         |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| API features                               | [docs/reference/apis/README.md](./docs/reference/apis/README.md)                                 |
| Webapp features (Django app/Javascript)    | [docs/reference/webapp/README.md](./docs/reference/webapp/README.md)                             |
| in Webapp, more specifically Django        | [docs/reference/webapp/django.md](./docs/reference/webapp/django.md)                             |
| in Webapp, more specifically Templating    | [docs/reference/webapp/templates.md](./docs/reference/webapp/templates.md)                       |
| in Webapp, more specifically Look and feel | [docs/reference/webapp/look-and-feel.md](./docs/reference/webapp/look-and-feel.md)               |
| Infrastructure                             | [docs/reference/infrastructure/provisioning.md](./docs/reference/infrastructure/provisioning.md) |
| Monitoring                                 | [docs/reference/infrastructure/monitoring.md](./docs/reference/infrastructure/monitoring.md)     |
| CI/CD                                      | [docs/reference/infrastructure/ci-cd.md](./docs/reference/infrastructure/ci-cd.md)               |
| Javascript (Stimulus/Maplibre/Turbo)       | [docs/reference/webapp/javascript.md](./docs/reference/webapp/javascript.md)                     |
| Airflow                                    | [docs/reference/data-platform/airflow.md](./docs/reference/data-platform/airflow.md)             |
| DBT                                        | [docs/reference/data-platform/dbt.md](./docs/reference/data-platform/dbt.md)                     |

## General Coding guidelines

- Nommage (et [Swift API Guidelines](https://www.swift.org/documentation/api-design-guidelines/))
- La base de code python suit les conventions décrites par [PEP8](https://peps.python.org/pep-0008/). Garanti en CI par `ruff`
- La base de code Typescript suit les conventions décrites par [TypeScript style guide](https://ts.dev/style/). Garanti en CI par `eslint` / `prettier`

### Project Structure

```txt
/
├── .github/           # CI/CD workflows
├── webapp/            # Application Django + Stimulus « Que faire de mes objets et déchets »
│   ├── core/          # Django configuration (settings, urls, wsgi)
│   ├── qfdmo/         # Main Django app (business models)
│   ├── qfdmd/         # Django app for CMS
│   ├── static/        # Compiled static assets
│   │   └── to_compile/ # TypeScript/JavaScript sources to compile
│   ├── templates/     # Django templates (HTML)
│   ├── unit_tests/    # Unit tests with pytest
│   ├── integration_tests/ # Integration tests with pytest
│   └── e2e_tests/     # End-to-end tests with Playwright
├── data-platform/     # Plateforme data (Airflow, dbt, notebooks…)
│   ├── dags/          # Airflow DAGs (clone, enrich, crawl, etc.)
│   └── dbt/           # dbt models for data transformation
├── docs/              # Documentation technique
├── infrastructure/    # Gestion et déploiement de l'infrastructure
├── docker-compose.yml # Exécution en local
├── nginx-local-only/  # Configuration Nginx pour le dev local
├── Makefile           # Commandes globales
├── scripts/           # Scripts hors webapp
└── pyproject.toml     # Dépendances Python (uv)
```

## 📝 Code Conventions

### Python

- Linter: Ruff (configuration in `pyproject.toml`)
- Formatting: Black (line-length: 88)
- Type hints: Use type hints when relevant
- Imports: Organized according to Django conventions (stdlib, third-party, local)
- Tests: pytest with pytest-django

## 🔍 Codebase Search

- Use `codebase_search` to understand flows
- Use `grep` to find exact occurrences

## 📚 Documentation

- Technical documentation is in `docs/` and published on GitHub Pages
- Specific READMEs are in each important subfolder
