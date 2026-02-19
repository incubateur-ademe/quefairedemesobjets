# Templates

## Main organization

- **`templates/ui/layout/`** — Global layout: `base.html`, `assistant.html`, error pages, partials (header, footer)
- **`templates/ui/pages/`** — Main pages (home, map, form, product page, actor page, configurator, etc.)
- **`templates/ui/components/`** — Reusable components (modals, map, search, product, actor, etc.)
- **`templates/ui/forms/widgets/`** — Form widgets (autocomplete, segmented control, etc.)
- **`templates/dsfr/`** — DSFR integration (global CSS/JS, pagination, etc.)

## Structure and splitting strategy

In this project, template splitting is used in a few specific situations:

- **Make a design element reusable** (DSFR component, custom component)
- **Make a template easier to read and maintain** by splitting it into smaller, focused units

We distinguish two main kinds of templates:

- A **component template** is considered reusable across multiple pages or features.
  It is named `component_name.html` (no leading underscore) and is usually placed in a shared or feature-agnostic directory.

- A **template fragment** is considered **local** to the template that uses it.
  It is named `_fragment_name.html` (with a leading underscore) and is placed in a subdirectory whose name matches the parent template file.

The goal is to keep the **top-level templates as flat and readable as possible**, and move complexity into smaller partials or reusable components.

### Example directory structure

For example, if we are working on the detail page template for an “actor” entity, and this page uses a `tag` component, we can use the following directory structure:

```text
shared
- tag.html        # reusable component template

acteur
- fiche.html      # main template for the actor detail page
- fiche           # directory for fragments used only by fiche.html
- - presentation.html
- - _tags.html
```

In this structure:

- `shared/tag.html` is a **reusable component template**.
- `acteur/fiche.html` is the **main page template**.
- Files inside `acteur/fiche/` are **fragments** used only by `fiche.html`:
  - `presentation.html` may be a larger sub-template (no underscore, still “local” to `fiche` by convention).
  - `_tags.html` is clearly identified as a fragment and is not meant to be used outside `fiche.html`.

### Example usage in a fragment

Example of the `_tags.html` fragment:

```html
{# _tags.html #} {% for tag in tags %} {% include "shared/tag.html" %} {% endfor
%}
```

In this example:

- The `_tags.html` fragment expects a `tags` variable in the context.
- For each `tag`, it includes the reusable component `shared/tag.html`.
- The `shared/tag.html` template is responsible for rendering a single tag.

## Django template locations and paths

In Django, templates are loaded from directories configured in `TEMPLATES` (for example, the global `templates/` directory and any app-specific `templates/` directories).

For this project:

- **Global templates** live in the top-level `templates/` directory.
- App-specific templates can also live under `app_name/templates/app_name/` if needed.
- Template names used in `{% include %}` or `{% extends %}` are always **relative to the templates root**, for example:
  - `shared/tag.html`
  - `acteur/fiche.html`

## Legacy templates

This convention was adopted during the project and **some legacy templates may not follow it yet**.

If you find templates that do not respect these rules:

- Prefer following the **current documented convention** for any **new** templates or refactors.
- When modifying legacy templates, you may progressively migrate them towards this structure (extract reusable components, create local fragments, rename files) if it does not break existing behavior and if it makes the codebase clearer.
