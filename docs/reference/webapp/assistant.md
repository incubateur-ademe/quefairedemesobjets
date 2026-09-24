# Assistant

## Objectif

Assistant V2 au tri, au réemploi et à la réparation : quatre écrans embarqués
en iframe (accueil, fiche objet, solutions sur carte, détail d'un lieu) et
l'endpoint GeoJSON qui alimente la carte. Le plan et les décisions (chapitres
00 à 10, ADR 0001 à 0010) vivent hors du code, sur la branche locale
`assistant-v2-specs` (`docs/explanations/assistant/`).

## Dépendances internes

Cette app ne possède **aucun modèle**. Elle orchestre :

| Source                  | Rôle                                              |
| ----------------------- | ------------------------------------------------- |
| `qfdmo.DisplayedActeur` | lieux affichés sur la carte et fiche d'un lieu    |
| `qfdmo.GroupeAction`    | les « gestes », leurs couleurs et libellés courts |
| `qfdmd.ProduitPage`     | fiche d'un objet et ses sous-catégories           |

## Dépendances externes

- **MapLibre GL** pour le rendu de la carte, chargé dynamiquement — il reste
  hors du bundle initial. Son worker est un bundle Parcel à part
  (`maplibre-worker.ts`, cible `worker`)
- **carte-facile** (IGN/DINUM) pour le fond de carte désaturé
- **BAN** (`data.geopf.fr`) pour l'autocomplétion d'adresse
- **Public Sans** (`@fontsource-variable/public-sans`), la police du Figma,
  auto-hébergée

## Structure

```text
assistant/
├── forms.py        SearchForm (accueil) et LieuxForm (GeoJSON)
├── parcours.py     objet + adresse transportés par l'URL, d'écran en écran
├── objets.py       résolution d'un libellé saisi vers une ProduitPage
├── consignes.py    consignes par geste, statiques en attendant #3284
├── lieu.py         ce que la fiche d'un lieu affiche
└── views/
    ├── pages.py    Home, Recherche, Produit, Solutions, Lieu
    ├── geojson.py  LieuxGeoJSONView
    ├── recherche.py / adresse.py   autocomplétions (JSON)
    └── mixins.py   TurboFrameMixin : gabarit réduit si en-tête Turbo-Frame
```

Tests : `unit_tests/assistant/` (seul dossier collecté par `make unit-test`).

## Routes

| URL                            | Vue                 | Réponse                |
| ------------------------------ | ------------------- | ---------------------- |
| `/assistant/`                  | `HomeView`          | HTML                   |
| `/assistant/recherche/`        | `SearchView`        | redirection vers fiche |
| `/assistant/objet/<slug>/`     | `ProduitView`       | HTML                   |
| `/assistant/solutions/`        | `SolutionsView`     | HTML (carte)           |
| `/assistant/lieu/<uuid>/`      | `LieuView`          | HTML                   |
| `/assistant/lieux.geojson`     | `LieuxGeoJSONView`  | GeoJSON                |
| `/assistant/recherche/objet`   | `ObjetSearchView`   | JSON                   |
| `/assistant/recherche/adresse` | `AdresseSearchView` | JSON                   |

Le contrat complet est dans le chapitre 10 des specs (branche
`assistant-v2-specs`).

### `lieux.geojson`

Paramètres, validés par `LieuxForm` : `geste` (code d'un `GroupeAction`,
obligatoire), `objet` (slug d'une fiche, facultatif), et soit `bbox` (zone
visible, forme Leaflet) soit `lon` + `lat`. Une bbox illisible renvoie `400`
sans repli sur le point.

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [2.35, 48.86] },
      "properties": { "uuid": "…", "nom": "…", "bonus": false }
    }
  ]
}
```

Au plus 20 lieux, triés par proximité. La couleur du pinpoint n'est pas
exposée : elle suit le geste choisi par l'usager, que le client connaît déjà.

## Budget de performance

| Endpoint        | Budget | Mesuré (p95, HTTPS) |
| --------------- | ------ | ------------------- |
| `lieux.geojson` | 50 ms  | 25 ms               |

L'en-tête `Server-Timing` de la réponse donne le temps passé en base ; le
lookbook l'affiche dans un overlay (`debug=True`). Les décisions qui rendent
ce chiffre possible sont consignées dans les ADR 0003 à 0006 des specs
(branche `assistant-v2-specs`).

## Tests

```bash
uv run pytest unit_tests/assistant               # endpoint, écrans, formulaires
npx jest static/to_compile/js/assistant          # logique de fusion des lieux
npx playwright test e2e_tests/assistant_carte    # carte en navigateur
npx playwright test e2e_tests/assistant          # écrans en navigateur
```
