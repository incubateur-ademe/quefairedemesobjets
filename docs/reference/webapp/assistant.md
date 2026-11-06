# Assistant

## Purpose

Assistant V2 for sorting, reuse and repair, embedded in an iframe. This first
brick sets the components (visible in the lookbook), the two search fields and
their endpoints; the screens come next.

## Dependencies

- `qfdmd.ProduitPage` and its search terms, for the objet suggestions.
- **BAN** (`data.geopf.fr`), through the `/api/v1/adresses` proxy.
- **Public Sans** (`@fontsource-variable/public-sans`), self-hosted.

## Structure

```text
assistant/
├── objets.py       objet suggestions
├── adresses.py     address suggestions (BAN proxy)
└── api.py          endpoints of the search fields: objets, adresses
```

The `assistant:home` and `assistant:produit` routes exist without a screen, so
that the middleware can resolve them.

## Tests

```bash
uv run pytest unit_tests/assistant
npx jest static/to_compile
```
