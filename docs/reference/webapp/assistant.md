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
- **Turbo Drive** actif : chaque écran est une page Django, Turbo remplace le
  `<body>` sans recharger, avec une View Transition ; la toile de la carte est
  un élément permanent qui survit aux changements d'écran. Les aperçus depuis
  le cache d'instantanés sont coupés (`turbo-cache-control: no-preview`) :
  Turbo n'anime qu'une fois par visite, et un aperçu prenait cette animation
  avant un remplacement sec par la page réelle
- **carte-facile** (IGN/DINUM) pour le fond de carte désaturé
- **BAN** (`data.geopf.fr`) pour l'autocomplétion d'adresse
- **Public Sans** (`@fontsource-variable/public-sans`), la police du Figma,
  auto-hébergée

## Structure

```text
assistant/
├── forms.py        SearchForm (accueil)
├── parcours.py     fiche + objet + adresse transportés par l'URL, d'écran en écran
├── objets.py       libellé saisi → ProduitPage, suggestions d'objets
├── adresses.py     suggestions d'adresses (proxy BAN)
├── consignes.py    consignes par geste, statiques en attendant #3284
├── lieu.py         ce que la fiche d'un lieu affiche
├── api.py          API publique v1 : lieux, gestes, objets, adresses
└── views/
    ├── pages.py    Home, Recherche, Produit, Solutions, Lieu
    └── mixins.py   TurboFrameMixin : gabarit réduit si en-tête Turbo-Frame
```

Tests : `unit_tests/assistant/` (seul dossier collecté par `make unit-test`).

## Routes

| URL                        | Vue             | Réponse                |
| -------------------------- | --------------- | ---------------------- |
| `/assistant/`              | `HomeView`      | HTML                   |
| `/assistant/recherche/`    | `SearchView`    | redirection vers fiche |
| `/assistant/objet/<slug>/` | `ProduitView`   | HTML                   |
| `/assistant/solutions/`    | `SolutionsView` | HTML (carte)           |
| `/assistant/lieu/<uuid>/`  | `LieuView`      | HTML                   |

Les écrans sont les premiers clients de l'[API publique v1](../apis/v1.md) :
la carte, les deux champs de recherche et le compteur de chaque bloc de la
fiche appellent `/api/v1/…`. Il n'existe pas de second chemin de code à tenir
au niveau.

Le contrat complet est dans le chapitre 10 des specs (branche
`assistant-v2-specs`).

### `/api/v1/lieux.geojson`

Paramètres, validés par `api.LieuxQuery` : `geste` (code d'un `GroupeAction`,
obligatoire, répétable), `fiche` (slug d'une fiche, facultatif), et soit `bbox`
(zone visible, forme Leaflet) soit `longitude` + `latitude`. Une bbox illisible
renvoie `422` sans repli sur le point.

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

| Endpoint                | Budget | Mesuré (p95, HTTPS) |
| ----------------------- | ------ | ------------------- |
| `/api/v1/lieux.geojson` | 50 ms  | 25 ms               |

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
