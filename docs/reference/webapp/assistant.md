# Assistant

## Purpose

Assistant V2 for sorting, reuse and repair: four screens embedded in an iframe
(home, objet fiche, solutions on a map, detail of a lieu).

## Internal dependencies

This app has **no model**. It orchestrates:

| Source                  | Role                                                |
| ----------------------- | --------------------------------------------------- |
| `qfdmo.DisplayedActeur` | lieux shown on the map and on the lieu page         |
| `qfdmo.GroupeAction`    | the « gestes » and their short labels               |
| `qfdmd.ProduitPage`     | an objet's fiche, its consignes grid, its synonymes |

## External dependencies

- **MapLibre GL** for the map, loaded dynamically, outside the initial bundle.
  Its worker is a separate Parcel bundle (`maplibre-worker.ts`, `worker`
  target). The base style (desaturated, from `carte-facile`) is served as a
  static file: `static/to_collect/assistant/carte-style.json`.
- **Turbo Drive**: each screen is a Django page, Turbo replaces the `<body>`
  with a View Transition. The map canvas is a permanent element that survives
  screen changes.
- **BAN** (`data.geopf.fr`), through the `/api/v1/adresses` proxy.
- **Public Sans** (`@fontsource-variable/public-sans`), self-hosted.

## Structure

```text
assistant/
├── forms.py        SearchForm (home)
├── parcours.py     fiche, objet, synonyme and address carried by the URL
├── objets.py       label or synonyme → ProduitPage, objet suggestions
├── adresses.py     address suggestions (BAN proxy)
├── solutions.py    gestes asked for and nearest places of the solutions screen
├── consignes.py    consignes per geste: the CMS grid, or static blocks
├── lieu.py         what the lieu page shows
├── api.py          endpoints of the screens: lieux.geojson, objets, adresses
└── views/
    ├── pages.py    Home, Recherche, Produit, Solutions, Lieu
    └── mixins.py   TurboFrameMixin: reduced template on a Turbo-Frame header
```

## Routes

| URL                        | View            | Response              |
| -------------------------- | --------------- | --------------------- |
| `/assistant/`              | `HomeView`      | HTML                  |
| `/assistant/recherche/`    | `SearchView`    | redirect to the fiche |
| `/assistant/objet/<slug>/` | `ProduitView`   | HTML                  |
| `/assistant/solutions/`    | `SolutionsView` | HTML (map)            |
| `/assistant/lieu/<uuid>/`  | `LieuView`      | HTML                  |

The screens call the [API v1](../apis/v1.md): the map (`/lieux.geojson`) and
the two search fields (`/objets`, `/adresses`).

The `synonyme` parameter (slug of a synonyme) shows that synonyme in the fiche's
search field; an unknown synonyme, or one attached to another fiche, is
ignored. It comes from the suggestions, or from `data-synonyme` in the embed
code.

### `/api/v1/lieux.geojson`

Parameters validated by `LieuxQuery` (`qfdmo/lieux_query.py`): `geste` (code of
a `GroupeAction`, required, repeatable), `fiche` (slug of a fiche, optional),
and either `bbox` (visible area) or `longitude` + `latitude`. An unreadable
bbox returns `422`.

At most 20 lieux, sorted by distance, within 20 km of a point. The
`Server-Timing` header gives the time spent in the database; the lookbook
shows it in an overlay (`debug=True`).

A new address starts a new search: the map forgets its lieux. Moving the map
keeps the ones still in view.

## Tests

```bash
uv run pytest unit_tests/assistant
npx jest static/to_compile
npx playwright test e2e_tests/assistant_
```
