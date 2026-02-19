# Cursor Guidelines - What to do with my objects

This file contains important guidelines for understanding and working effectively on this project.

## 🏗️ General Architecture

### Tech Stack

- Administration commands: in the root `Makefile` and `scripts/`
- Backend (webapp): Django 5.2+ (Python 3.12), dependency management and python commands with `uv`
- Frontend (webapp): TypeScript with Stimulus 3.x and Turbo 8.x and templating avec Django templates
- Build (webapp): Parcel 2.x
- Orchestration (data-platform): Apache Airflow 2.11+
- Data (data-platform): PostgreSQL with postgis extension, dbt for transformation
- Design System: DSFR (French State Design System) via `django-dsfr`

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

### TypeScript/JavaScript

- Linter: ESLint with "love" config
- Formatting: Prettier (trailing comma: all, printWidth: 88, semi: false)
- Framework: Stimulus for controllers, Turbo for navigation
- Build: Parcel compiles `static/to_compile/` to `static/compiled/`

### Naming conventions

- Python: snake_case for variables/functions, PascalCase for classes
- TypeScript: camelCase for variables/functions, PascalCase for classes
- Files: snake_case for Python, kebab-case for TypeScript

## 🎯 Important Patterns

### Stimulus Controllers

- Controllers are in `webapp/static/to_compile/controllers/`
- Use Stimulus targets and values
- Export as `export default class extends Controller`
- Structure example:

```typescript
import { Controller } from "@hotwired/stimulus";

export default class extends Controller<HTMLElement> {
  static targets = ["targetName"];
  declare readonly targetNameTarget: HTMLElement;

  connect() {
    // Initialization
  }
}
```

### Django Views

- Use class-based views when appropriate
- Prefer `LoginRequiredMixin` for protected views
- Use `prefetch_related` and `select_related` to optimize queries
- Admin views are mainly in `webapp/qfdmo/admin.py` and `webapp/qfdmd/admin.py`

### Django Templates

- Use partials in `webapp/templates/data/_partials/` for reusability
- Base layout is in `webapp/templates/ui/layout/base.html`
- Use template tags from `webapp/core/templatetags/` for reusable logic

### Airflow DAGs

- Organized by domain in `data-platform/dags/` (clone, enrich, crawl, etc.)
- Use shared utilities in `data-platform/dags/shared/`
- DAG organization:
  - DAGs are in `./dags/<EPIC>/dags/`
  - Tasks are in `./dags/<EPIC>/tasks/`
  - Wrappers between Airflow and business code in `./dags/<EPIC>/tasks/airflow_logic/`
  - Business logic in `./dags/<EPIC>/tasks/business_logic/` independent of Airflow

## 🔧 Useful Tools and Commands

### Development

- `npm run watch`: Watch mode for Parcel (automatic compilation)
- `npm run build`: Production build
- `npm run lint`: TypeScript/JavaScript linter
- `npm run format`: Format code with Prettier

### Tests

- `npm test`: Jest tests (webapp)
- `npm run e2e_test`: Playwright tests (webapp)
- `uv run pytest` Python tests, or:
  - `make unit-test`: unit tests (webapp)
  - `make integration-test`: integration tests (webapp)
  - `make dags-test`: DAG tests (data-platform)

### Database

- Django migrations are in `webapp/*/migrations/`
- dbt models are in `data-platform/dbt/models/`

## 🎨 Design System (DSFR)

- Use DSFR components via `django-dsfr`
- Colors and icons used are tracked in `dsfr_hacks/`
- Respect DSFR accessibility guidelines

## 📦 Important Dependencies

### Backend

- `django-ninja`: REST API
- `django-import-export`: Data import/export
- `rapidfuzz`: Fuzzy matching for suggestions
- `django-dsfr`: Design System integration

### Frontend

- `@hotwired/stimulus`: Controller framework
- `@hotwired/turbo`: SPA-like navigation
- `maplibre-gl`: Mapping
- `@gouvfr/dsfr`: Frontend Design System

### API

- `NinjaAPI` : Build api and its documentation

details about how build and test API can be found here : [api.AGENTS.md](./api.AGENTS.md)

## 🚀 Development Workflow

1. Frontend modifications (webapp) :

- Edit in `webapp/static/to_compile/`, Parcel compiles automatically
- `webapp/templates/` Django templating engine

1. Backend modifications (webapp) : Edit directly, Django reloads automatically in dev
1. New features : Create migrations if necessary, test with pytest (`uv run pytest`)
1. E2E tests : Use Playwright for e2e tests in `webapp/e2e_tests/`

## ⚠️ Important Points

- Django Migrations: Always create migrations for model changes
- Frontend compilation: Check that Parcel has compiled properly before committing
- Tests: Tests must pass before merging
- Secrets: Use `python-decouple` for environment variables, never hardcode secrets, new secrets must be referenced in `.env.template`
- Airflow: DAGs must be idempotent and handle errors gracefully

## 📚 Documentation

- Technical documentation is in `docs/` and published on GitHub Pages
- Specific READMEs are in each important subfolder

## 🔍 Codebase Search

### Key Files to Know

- `webapp/core/settings.py`: Django configuration
- `webapp/core/urls.py`: Main URLs
- `webapp/static/to_compile/admin.ts`: JS code entry point

### Search Patterns

- Use `codebase_search` to understand flows
- Use `grep` to find exact occurrences
