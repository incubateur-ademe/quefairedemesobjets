# Review screen of the SOURCE suggestions

A dedicated screen, for superusers only, to review the suggestions of the
**SOURCE** cohortes (`SOURCE_AJOUT`, `SOURCE_MODIFICATION`, `SOURCE_SUPRESSION`)
quickly: thousands of groupes, keyboard first, mass actions, optimistic UI.

- URL: `/data/revue/` (client-side routing below this path)
- API: `/api/suggestions/` (see [the API reference](../apis/suggestions.md))
- Front: React + TypeScript + Web Awesome, in its own npm package
  `webapp/revue-front/`, built independently of the rest of the webapp

The Django admin screens of the suggestions are **not** modified: both live in
parallel. The review screen only adds code (`webapp/data/revue/`,
`webapp/revue-front/`) and a few fields to the models.

## Concepts

- `SuggestionCohorte` 1→N `SuggestionGroupe` 1→N `SuggestionUnitaire` (SU).
- A **ligne de suggestion** is, for a groupe, the set of SU sharing the same tuple
  of `champs` (ex: `(latitude, longitude)`), whatever their `suggestion_modele`
  (`Acteur`, `RevisionActeur`, `ParentRevisionActeur`). Validating a ligne
  validates all its SU.
- The **statut of a ligne** is derived: the statut of its groupe once the groupe
  is not `AVALIDER` anymore, otherwise `ATRAITER` when all its SU are validated.
- Validating only sets the statut to `ATRAITER`: suggestions are applied later by
  the existing DAG (`apply_suggestions_groupe`).
- Each human decision is traced on the groupe and its SU (`decision_par`,
  `decision_le`); « remettre à valider » clears them.

### Rules of the SOURCE review policy

The rules are grouped by `type_action` in `data/revue/policies.py` and exposed to
the front as **capabilities** computed for each groupe and ligne: the front has no
rule of its own for a type.

- All the groupe or nothing: a ligne is never refused alone, only the groupe.
- Lignes are validated one by one; the groupe is validated with its last ligne.
  Validating the groupe validates all its lignes.
- Only elements `AVALIDER` can be decided; `ENCOURS`, `SUCCES`, `ERREUR` are read
  only.
- « Remettre à valider »: a validated / refused groupe, or a groupe to validate
  having validated lignes, goes back to validate with all its lignes. A ligne of a
  refused groupe reopens the whole groupe.
- SU `Acteur` (the source) are never corrected. Corrections are SU on
  `RevisionActeur` (« Correction ») and `ParentRevisionActeur` (« Parent »),
  created when needed. A correction is validated like the admin does
  (`update_suggestion_groupe`, `RevisionActeur.full_clean()`).
- **Report** (▶ / ⏩) copies the suggestion of the source to the correction or the
  parent, except the non reportable fields
  (`SuggestionSourceModel.get_not_reportable_on_*_fields`).
- `SOURCE_AJOUT`: no acteur yet, no parent; `SOURCE_SUPRESSION` is a modification
  whose only ligne is the `statut` field.

## Screens

| Screen                               | Content                                                                                                                                                                                                      |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Cohortes (`/data/revue/`)            | SOURCE cohortes having groupes: quick filters, structured filters (with the keys of `metadata`), sort, pagination, progress, logs (side panel, Excel export).                                                |
| Review (`/data/revue/cohortes/<id>`) | Counters, view « Groupes » or « Lignes », « Afficher » (to validate / all), structured filters, tuples of champs, pagination, selection and mass actions.                                                    |
| Detail of a groupe (modal)           | Suggestions, acteur displayed, localisation (map, draggable markers saved on release, Annuaire des entreprises localisation), Annuaire des entreprises (entreprise and établissement of each SIRET / SIREN). |

Every navigation state (view, filters, tuples, page, page size, opened modal and
tab, logs panel) is in the URL: a page can be shared and is restored on reload.

### Keyboard

A single cursor: `↑` / `↓` (groupe header → its lignes → next groupe, and the
neighbour page at an end), `A` validates the element under the cursor and moves
on, `R` refuses the groupe (view Groupes), `U` puts back to validate, `X` checks
the element (mass actions), `⏎` opens the detail of the groupe, `/` opens the
filters, `Échap` closes. The list is in the « ? raccourcis » tooltip.

### Writes

- **Optimistic**: the table is updated before the server answers and rolled back
  on error. Only errors are notified (no success notification).
- **Concurrency**: each write sends the `modifie_le` of the groupe; a groupe changed
  meanwhile answers `409` with its current state, which replaces it on screen.
  Writes on a same groupe are queued, each with the `modifie_le` of the previous
  answer, so chained keyboard decisions do not conflict.
- **Decided elements stay on screen** until the list changes (filters, view,
  tuples, « Afficher »), otherwise the pagination would skip elements.
- **Mass actions**, on the checked elements of the page or on « all the elements
  matching the filter » (minus the unchecked ones), like the Django admin. Each
  button gives the number of elements it really changes. A refusal, a « whole
  filter » selection or more than 50 elements ask for a confirmation. Decisions
  are bulk SQL updates; reports of more than 1000 groupes run in a django-tasks
  task (the `db_worker` must run).

## Code organisation

### Backend: `webapp/data/revue/`

| Module                     | Role                                                                            |
| -------------------------- | ------------------------------------------------------------------------------- |
| `api.py`                   | django-ninja router mounted on `/api/suggestions/` (thin handlers)              |
| `auth.py`                  | `SuperuserSessionAuth`: Django session + CSRF; 401 anonymous, 403 non superuser |
| `views.py`, `urls.py`      | Django page `/data/revue/…` serving the React application                       |
| `policies.py`              | Review policy per `type_action`                                                 |
| `filters.py`               | Structured filters engine (whitelist, operators, compilation to `Q`)            |
| `cohortes.py`              | Screen 1: cohortes, logs                                                        |
| `revue.py`                 | Screen 2: filters of the groupes and lignes, querysets, counters                |
| `lignes.py`                | Serialization of the groupes, lignes and capabilities                           |
| `services.py`              | Unit writes (lock, conflict check, capabilities)                                |
| `masse.py`                 | Selection, preview and run of the mass actions, report task                     |
| `detail.py`, `annuaire.py` | Modal: displayed acteur, map points, Annuaire des entreprises proxy             |
| `exports.py`               | Excel export of the logs                                                        |

Shared statut writes are in `webapp/data/services/suggestion_statut.py`.

### Front: `webapp/revue-front/`

An independent npm package (workspace of the root `package.json`) with its own
Parcel, TypeScript, Jest and ESLint configurations.

| Path                          | Role                                                                                         |
| ----------------------------- | -------------------------------------------------------------------------------------------- |
| `src/main.tsx`, `src/App.tsx` | Entry point: bootstrap data, React Query, router                                             |
| `src/router.tsx`              | Minimal client-side router (state in the search params)                                      |
| `src/api/`                    | Typed client (`openapi-fetch`), generated types, queries, optimistic mutations, mass actions |
| `src/domain/`                 | Filter model, statuts, external links, formats                                               |
| `src/screens/`                | Cohortes, review (views, cells, mass bar), modal of a groupe (map)                           |
| `src/wa.ts`                   | Web Awesome React wrappers used (replaced by plain elements in Jest)                         |
| `src/icons.ts`                | Local icon library (Remix Icon): no CDN                                                      |

Main dependencies: React 19, TanStack Query, Web Awesome 3, MapLibre (map of the
modal, with its worker inlined as for the webapp), `@socialgouv/codes-naf` (labels
of the NAF codes).

## Running locally

```bash
# Database and superuser (admin / admin)
docker compose --profile lvao up -d lvao-webapp-db
make -C webapp migrate
make -C webapp createsuperuser-example

# Servers: Django, and the watch of the review screen
make -C webapp runserver
npm install
npm -w webapp/revue-front run watch
```

Then log in on <http://localhost:8000/admin/> and open
<http://localhost:8000/data/revue/>. The API is documented on
<http://localhost:8000/api/docs> (tag « Revue suggestions »).

The screen works on the cohortes of the local database. The command
`seed_revue_suggestions` creates a deterministic dataset (more than 100 groupes and
500 lignes) **for the tests only**: it refuses any database but `test_*` and
`webapp_sample`, unless a database is explicitly allowed by name
(`--allow-database`), and never runs in production or staging.

## Build and deployment

| Command                      | Effect                                                        |
| ---------------------------- | ------------------------------------------------------------- |
| `npm run build`              | Builds the webapp assets (unchanged)                          |
| `npm run build:revue`        | Builds the review screen into `webapp/static/compiled/revue/` |
| `npm run scalingo-postbuild` | Both, run by Scalingo instead of `build`                      |

The Dockerfile and the `setup-frontend` CI action also build the review screen.
There is no code splitting: whitenoise only keeps hashed files, which would break
chunks loaded by a relative URL.

## API types

The TypeScript types of the API are generated from the OpenAPI schema and
committed:

```bash
npm -w webapp/revue-front run api:types
```

The CI job `revue_api_types` fails when they are not up to date.

## Tests

| Command                                            | Scope                                                                             |
| -------------------------------------------------- | --------------------------------------------------------------------------------- |
| `make -C webapp unit-test` / `integration-test`    | Filters, policies, services, API (`unit_tests/data/`, `integration_tests/revue/`) |
| `npm -w webapp/revue-front run test`               | Front (Jest + Testing Library)                                                    |
| `npm -w webapp/revue-front run typecheck` / `lint` | Typecheck, ESLint                                                                 |
| `make -C webapp e2e-test`                          | Playwright, `e2e_tests/revue_suggestions.spec.ts` (seed created before each test) |
