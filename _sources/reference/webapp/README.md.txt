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

for more details about js/parcel configuration, read the [package.json](../../../webapp/package.json) file.

#### PostCSS

Parcel includes PostCSS, which is extended in this project to support Tailwind and [_CSS nesting_](https://www.w3.org/TR/css-nesting-1/).

### DSFR and Tailwind

The **French State Design System (DSFR)** is used to comply with accessibility and identity requirements for French public services. It is combined with **Tailwind CSS** for layout and styling.

More details in [look-and-feel.md](./look-and-feel.md)

## 🔧 Useful Tools and Commands

from `webapp` folder

### Development

- `npm run watch`: Watch mode for Parcel (automatic compilation)
- `npm run build`: Production build
- `npm run lint`: TypeScript/JavaScript linter
- `npm run format`: Format code with Prettier

### Tests

From the **`webapp/`** directory (after `uv sync`):

- `npm test`: Jest tests
- `npm run e2e_test` / `make e2e-test`: Playwright (e2e) tests
- `uv run pytest` or:
  - `make unit-test`: unit tests
  - `make integration-test`: integration tests

DAG / Airflow Python tests live in **`data-platform/`**: `cd data-platform && uv sync && make dags-test`.

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
