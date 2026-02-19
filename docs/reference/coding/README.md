# Code Guidelines

## Use of French and English languages

We follow industry rules and standards, which we enforce on each commit and Pull Request with tools such as `ruff` or `eslint`.

However, this project is developed and operated by the French State and must be easily usable and manageable by as many people as possible. We therefore apply a specific rule regarding the use of the French versus the English language, and have defined the use cases for these two languages.

### 🇫🇷 In French

For citizens, administrations, administrators, and the “Longue vie aux objets” team:

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

From root folder:

- **Python**
  - **Lint**: run `make check-format` at the root of the project.
  - **Format**: run `make format` to apply formatting.

From `webapp` folder:

- **TypeScript**
  - **Lint**: run `npm run lint` from the project root to check the frontend code.
  - **Format**: run `npm run format` to apply Prettier on the frontend code.
