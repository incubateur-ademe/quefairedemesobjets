# Webapp

The webapp is the Django application that serves the «Que faire de mes objets» website.

It combined technologies :

- **Django** (and its apps),
- **Django templates** to render html,
- **JavaScript** (TypeScript compiled with Parcel)
- **Official french gouv design system** (DSFR used together with Tailwind).

## Overall structure

### Django and apps

The backend is a **Django** project whose central configuration lives in `core/` (settings, URLs, templatetags, context processors). Business logic is split across several **Django applications**:

- **core** — Configuration, URLs, shared templatetags and context processors
- **qfdmo** — Core business (models, views, forms of the main tool)
- **qfdmd** — CMS and content (pages, middleware, multi‑site integration)
- **infotri** — Infotri module (configurator, dedicated forms)
- **search** — Search
- **stats** — Statistics
- **data** — Data management and suggestions (admin, import/export)

Views, forms, and models are organised by app; templates and frontend assets are shared at the project level.

### Templates (Django)

**Templates** use the **Django** template engine (syntax `{% block %}`, `{% include %}`, `{% load %}`, etc.).

The organization and the splitting conventions (components vs local fragments with `_` prefix) are detailed in the frontend documentation [templates.md](templates.md).

### JavaScript (TypeScript and Parcel)

The frontend is written in **TypeScript** and compiled with **Parcel**.

- **Sources to compiled**: `static/to_compile/` (`.ts` entry points, Stimulus controllers, shared modules, styles)
- **Sources to collect**: `static/to_collect/` additionnal assets
- **Output**: `static/compiled/` (files served by Django via `STATICFILES_DIRS`)

Main entry points: `qfdmo.ts`, `qfdmd.ts`, `admin.ts`, and the embed bundles (`embed/assistant.ts`, `embed/carte.ts`, `embed/formulaire.ts`, `embed/infotri.ts`, etc.).

The frontend stack uses **Stimulus** for controllers and **Turbo** for navigation. Scripts are loaded in layouts (e.g. `base.html`) via `{% static 'qfdmo.js' %}` tags.

for more details about js/parcel configuration, read the [webapp `package.json`](../../../webapp/package.json) file. The frontend uses an **npm workspace**: `webapp/` is declared in the [root `package.json`](../../../package.json) and there is a single `package-lock.json` at the repo root.

#### PostCSS

Parcel includes PostCSS, which is extended in this project to support Tailwind and [_CSS nesting_](https://www.w3.org/TR/css-nesting-1/).

### DSFR and Tailwind

The **French State Design System (DSFR)** is used to comply with accessibility and identity requirements for French public services. It is combined with **Tailwind CSS** for layout and styling.

More details in [look-and-feel.md](./look-and-feel.md)

## 🔧 Useful Tools and Commands

npm is an **npm workspace** rooted at the repo root (`webapp/` is the only workspace). Install dependencies once with `npm ci` from the repo root, then run scripts either from `webapp/` or with `--workspace webapp`.

### Development

From `webapp/`:

- `make runserver`: Django dev server **and** django-tasks worker (`db_worker`) for background admin actions
- `npm run watch`: Watch mode for Parcel (automatic compilation)
- `npm run build`: Production build (also available from root via `npm run build`)
- `npm run lint`: TypeScript/JavaScript linter
- `npm run format`: Format code with Prettier

### Tests

- `npm test --workspace webapp`: Jest tests (from the repo root)
- `npm run e2e_test --workspace webapp` / `make e2e-test`: Playwright (e2e) tests
- `uv run pytest` or, from `webapp/`:
  - `make unit-test`: unit tests
  - `make integration-test`: integration tests

DAG / Airflow Python tests live in **`data-platform/`**: run `uv sync --group dev --group notebook` from root, then `make dags-test`.

#### Running E2E tests locally

E2E tests run against a dedicated `webapp_sample` database (kept separate from your
dev `webapp` database) on the same Postgres container, so you don't have to mutate
the dev data you're working with. The connection is configured by `DB_WEBAPP_SAMPLE`
in `.env` (see `.env.template`); the dev `DATABASE_URL` is left untouched.

The sample is built entirely locally by the Airflow DAG `compute_sample_acteur`,
from your restored `webapp` database. No remote sample database is copied.

```bash
# from repo root — checks prerequisites, runs the DAG, prepares the webapp
make e2e-prepare

# prepare + run the Playwright tests in one go
make e2e
```

`make e2e-prepare` fails with an explicit message when a prerequisite is missing
(Docker down, `.env` absent, a port squatted by another process, an empty
`webapp` database, a broken `postgres_fdw` bridge). It requires a restored
production database — run `make db-restore-local-from-prod` first.

Rebuilding the sample takes a few minutes. When iterating on tests and the
sample is already up to date, skip the DAG:

```bash
make e2e-prepare-fast   # migrations, search index and JS build only
make webapp-e2e-test
```

See [create_webapp_sample_db.md](../../how-to/development/create_webapp_sample_db.md)
for the full pipeline and how to trigger the DAG from the Airflow UI.

See [tests_e2e.md](../../how-to/development/tests_e2e.md) for how to write new E2E tests.

## ⚠️ Important Points

- Django Migrations: Always create migrations for model changes
- Frontend compilation: Check that Parcel has compiled properly before committing
- Tests: Tests must pass before merging
- Secrets: Use `python-decouple` for environment variables, never hardcode secrets, new secrets must be referenced in `.env.template`
- Airflow: DAGs must be idempotent and handle errors gracefully

```{toctree}
:maxdepth: 2

templates.md
look-and-feel.md
javascript.md
django.md
internationalization.md
```
