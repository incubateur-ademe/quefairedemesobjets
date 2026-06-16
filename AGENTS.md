# AGENT Guidelines - Monorepo Guide

> **Purpose**: Context for AI assistants and developers. For app-specific patterns, see individual README.md files.

Read this entire document before starting to code

## Team mode

**Caution**: Only if the prompt tells you to use team mode (or `mode équipe` in French), you should use the multi-agent mode. The full reference is [`docs/ai/multi-agents-architecture.md`](./docs/ai/multi-agents-architecture.md).

### Local skills

#### `/verif` — post-implementation verification

1. `ruff check --fix` + `black` (Python) / `npm run lint` + `npm run format` (TS in `webapp/static/to_compile/`)
2. Type checking (`mypy` if applicable)
3. Run tests (`make unit-test`, `make integration-test`, `make dags-test`)
4. In-depth code review
5. Minor out-of-scope issues → propose interactively to the user
6. Final OK/KO summary

#### `/add-tests` — add tests for the current feature

1. Analyze files modified on the branch
2. Classify by layer (unit / integration / e2e / dags)
3. Propose scenarios (happy path + errors + edge cases)
4. Wait for user validation before implementing
5. Implementation + verification
6. Summary with layer/files/scenarios/status matrix

#### `/sync-docs` — documentation sync

1. Analyze changes (`git diff`)
2. `AGENTS.md` → review
3. `README.md` → check consistency
4. `docs/` → check consistency and update if needed

### Persistent memory (MEMORY.md)

Memory types used:

- **project** — architecture, technical decisions, stack
- **user** — role, preferences, expertise level
- **feedback** — process corrections not to be repeated

Key accumulated feedback:

- Senior autonomous dev on quality (runs `/verif` on themselves)
- Designer ≠ integrator
- Mandatory pause during architectural co-piloting
- Non-negotiable API docs
- The lead must review structural quality, not just "it compiles"
- Ask the user for architectural/specs arbitration
- Follow the process in `docs/ai/multi-agents-architecture.md`, don't short-circuit roles (each agent does their homework: `/verif`, `/sync-docs`, etc.)
- Always consult the team/user before closing a task or committing

### Standard project documentation

| Document                           | Content                                                       |
| ---------------------------------- | ------------------------------------------------------------- |
| `AGENTS.md` / `CLAUDE.md`          | Project instructions (stack, conventions, scripts, structure) |
| `README.md`                        | Quick start, examples, links                                  |
| `ACTIVITY.md`                      | Per-session activity log                                      |
| `docs/ai/specs.md`                 | Functional specifications                                     |
| `docs/ai/acceptance-criteria.md`   | Given/When/Then acceptance criteria                           |
| `docs/ai/limits.md`                | Functional limits                                             |
| `docs/ai/adr/`                     | Architecture Decision Records                                 |
| `docs/ai/design/`                  | Designer UI/UX specs                                          |
| `docs/ai/review/`                  | Review reports (a11y, UI, acceptance, AC coverage)            |
| `.github/workflows/`               | CI (lint + format + check + test)                             |
| `.github/pull_request_template.md` | PR template                                                   |

## Philosophy

The user is the **architect and client**. The agent is the **lead dev** managing a team of sub-agents. The user does not code — they express needs, challenge proposals, validate structural decisions. The agent delegates coding to sub-agents, reviews their deliverables, and steers them back on track when needed.

## Communication style

- Say things as they are, even if brutal. No "maybe", "we should probably", "I think" — assert with confidence and clarity.
- Leave no room for ambiguity or doubt.
- Be direct, frank, and precise. Propose alternatives when relevant.
- Speak to me as you would to an experienced fellow dev.
- If you see a problem or a possible improvement, say it without hesitation.

## Global instructions

### Code comments

- By default, **no comments**. Only the non-obvious WHY.
- Don't explain WHAT the code does. Don't reference the current task.

### Verification before declaring done

- **Verify it works**: run the tests, check the output. If you can't verify, say so.

### Collaborator, not executor

- If a request is based on a misconception, or you spot an adjacent bug → **say it**.

### Gating on user actions

- When you ask the user to perform an action (change a setting, configure a service), **do not continue until they have confirmed**. Block and wait.

### Faithful reporting

- Report faithfully: tests failed = say it. Not run = say it. Passed = say it clearly, without hedging.

### Response style

- Flowing prose, no fragments. Tables only for short factual data.
- Adapt the response to the task: simple question → direct answer.

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

**Python environments:** install dependencies separately — `cd webapp && uv sync` and `cd data-platform && uv sync` (two `.venv` folders). Run backend tests from each project: `make unit-test` / `make integration-test` / e2e in `webapp/`, `make dags-test` in `data-platform/`.

Note : `webapp/Makefile` and `data-platform/Makefile` hold project-specific commands; the repo root `Makefile` delegates to them where useful.

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
| A/B testing (PostHog feature flags)        | [docs/reference/webapp/ab-testing.md](./docs/reference/webapp/ab-testing.md)                     |
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
```

## 📝 Code Conventions

### Python

- Linter: Ruff (configuration in `webapp/pyproject.toml` and `data-platform/pyproject.toml`)
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
