# Assistant

## Objectif

Parcours de recherche « que faire de mon objet » : l'usager saisit un objet et
une adresse, voit les gestes possibles, puis les lieux correspondants sur une
carte.

Le plan d'implémentation complet vit dans
[docs/explanations/assistant](../../docs/explanations/assistant/README.md).

## Dépendances internes

Cette app ne possède **aucun modèle**. Elle orchestre :

| Source                  | Rôle                                            |
| ----------------------- | ----------------------------------------------- |
| `qfdmd.ProduitPage`     | fiches produit (Wagtail), leurs sous-catégories |
| `qfdmo.DisplayedActeur` | lieux affichés sur la carte                     |
| `qfdmo.GroupeAction`    | les « gestes » et leurs couleurs                |
| `search.SearchTerm`     | moteur de recherche d'objet                     |

## Dépendances externes

- **BAN** (`data.geopf.fr`) pour le géocodage d'adresse, via le proxy existant
- **MapLibre GL** pour le rendu de la carte, chargé dynamiquement
- **carte-facile** (IGN/DINUM) pour le fond de carte désaturé

## Routes

| URL                          | Vue                  | Réponse |
| ---------------------------- | -------------------- | ------- |
| `/assistant/`                | `HomeView`           | HTML    |
| `/assistant/objet/<slug>/`   | `ProduitView`        | HTML    |
| `/assistant/solutions/`      | `SolutionsView`      | HTML    |
| `/assistant/lieu/<uuid>/`    | `LieuView`           | HTML    |
| `/assistant/lieux.geojson`   | `LieuxGeoJSONView`   | GeoJSON |
| `/assistant/recherche/objet` | `RechercheObjetView` | JSON    |

Le contrat de chaque paramètre est décrit dans
[10-contrat-url](../../docs/explanations/assistant/10-contrat-url.md).

## Contrat GeoJSON

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

| Endpoint          | Budget | Mesuré (p95, HTTPS) |
| ----------------- | ------ | ------------------- |
| `lieux.geojson`   | 50 ms  | 25 ms               |
| `recherche/objet` | 50 ms  | 20-48 ms            |

Les décisions qui rendent ces chiffres possibles sont consignées en
[ADR 0004 à 0007](../../docs/explanations/assistant/adr/README.md).

## Tests

```bash
make unit-test                                   # vues et endpoints
npx jest static/to_compile/js/assistant          # logique métier du client
npx playwright test e2e_tests/assistant_carte    # carte en navigateur
```
