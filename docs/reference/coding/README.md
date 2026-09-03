# Code Guidelines

## Use of French and English languages

We follow industry rules and standards, which we enforce on each commit and Pull Request with tools such as `ruff` or `eslint`.

However, this project is developed and operated by the French State and must be easily usable and manageable by as many people as possible. We therefore apply a specific rule regarding the use of the French versus the English language, and have defined the use cases for these two languages.

### 🇫🇷 In French

For citizens, administrations, administrators, and the “Que faire de mes objets et déchets” team:

- Git/GitHub commits and Pull Requests
- Names and fields of database tables

### 🇬🇧 In English

In the code, for technical teams:

- Function names
- Variable names
- Error messages in exceptions
- Comments in the code
- Technical documentation in markdown files

## Accepted side effects

Some variables combining an object name and a suffix or prefix may be in “Franglais”.

Example: `acteur_by_id`

## Python and TypeScript coding guidelines

- Naming (see also the [Swift API Guidelines](https://www.swift.org/documentation/api-design-guidelines/))
- The Python codebase follows the conventions described in [PEP 8](https://peps.python.org/pep-0008/). This is enforced in CI by `ruff`.
- The TypeScript codebase follows the conventions described in the [TypeScript style guide](https://ts.dev/style/). This is enforced in CI by `eslint` / `prettier`.

### Local linting and formatting

Python uses a **single uv workspace** at the repo root (`webapp/` and `data-platform/` are members, one `uv.lock`). From the **repository root**:

- **Python (Black + Ruff + SqlFluff)**: `make check-format` runs checks in `data-platform/` then `webapp/`.
- **Apply Python formatting**: `make format`.

You can also run `make check-format` / `make format` inside `webapp/` or `data-platform/` alone.

From the repo root (after `uv sync --all-packages --group dev --group webapp-dev` and `npm ci`):

- **TypeScript**
  - **Lint**: `npm run lint --workspace webapp`
  - **Format**: `npm run format --workspace webapp` (Prettier)
