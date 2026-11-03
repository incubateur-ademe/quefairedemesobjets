# Assistant

## Objectif

Assistant V2 au tri, au réemploi et à la réparation, embarqué en iframe. Cette
première brique pose les composants (visibles dans le lookbook), les deux
champs de recherche et leurs endpoints ; les écrans viennent ensuite.

## Dépendances

- `qfdmd.ProduitPage` et ses termes de recherche, pour les suggestions d'objets.
- **BAN** (`data.geopf.fr`), via le proxy `/api/v1/adresses`.
- **Public Sans** (`@fontsource-variable/public-sans`), auto-hébergée.

## Structure

```text
assistant/
├── objets.py       suggestions d'objets
├── adresses.py     suggestions d'adresses (proxy BAN)
└── api.py          endpoints des champs de recherche : objets, adresses
```

Les routes `assistant:home` et `assistant:produit` existent sans écran, pour
que le middleware puisse les résoudre.

## Tests

```bash
uv run pytest unit_tests/assistant
npx jest static/to_compile
```
