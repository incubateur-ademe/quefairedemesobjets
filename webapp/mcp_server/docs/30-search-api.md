# Interrogation de l'API ADEME `/lines`

Cette API expose chaque acteur du jeu de données comme une ligne JSON
filtrable. Elle est servie par la plateforme open-source **data-fair**.

- **Endpoint** : `https://data.ademe.fr/data-fair/api/v1/datasets/wvw1zecq4f4gyvonve5j0hr7/lines`
- **Schéma JSON** : <https://data.ademe.fr/data-fair/api/v1/datasets/wvw1zecq4f4gyvonve5j0hr7/schema?mimeType=application%2Fschema%2Bjson>
- **Documentation API** : <https://data.ademe.fr/datasets/longue-vie-aux-objets-acteurs-de-leconomie-circulaire/api-doc>
- **Coût** : gratuit, sans clé d'API

## Paramètres principaux

| Paramètre      | Type                   | Description                                                                    |
| -------------- | ---------------------- | ------------------------------------------------------------------------------ |
| `geo_distance` | `lon:lat:rayon_metres` | Filtre géographique. Ex. `2.35:48.86:5000` (5 km autour du Louvre).            |
| `qs`           | string                 | Filtre avancé style Lucene. Ex. `qs=reparer:"velo"`.                           |
| `q`            | string                 | Recherche plein-texte simple sur tous les champs.                              |
| `sort`         | string                 | Tri. `_geo_distance` pour trier par proximité. Préfixer par `-` pour inverser. |
| `size`         | int                    | Nombre de résultats par page (max 10000). Recommandé : `size=10`.              |
| `select`       | string[]               | Colonnes à retourner (réduit la taille de la réponse).                         |
| `format`       | string                 | `json` (défaut), `csv`, `geojson`, `xlsx`…                                     |

## Filtrer par action et par sous-catégorie : la syntaxe `qs`

Chaque action (`reparer`, `donner`, etc.) est une **colonne** du jeu de données
qui contient une **liste de codes sous-catégorie séparés par `|`**.

Exemple de cellule :

```
reparer = "luminaire | materiel_hifi_et_video | velo | vetement"
```

Pour chercher les acteurs qui **réparent les vélos** :

```
qs=reparer:"velo"
```

Pour chercher ceux qui réparent **vélos OU vêtements** :

```
qs=reparer:"velo" OR reparer:"vetement"
```

Pour combiner action + autre filtre (ex. ne garder que les ressourceries) :

```
qs=reparer:"velo" AND type_dacteur:"ess"
```

## Exemple complet : « réparer un téléphone à Paris »

1. Géocoder « Paris » via BAN → `lon=2.3522, lat=48.8566`.
2. Construire l'URL :

```
https://data.ademe.fr/data-fair/api/v1/datasets/wvw1zecq4f4gyvonve5j0hr7/lines
  ?geo_distance=2.3522:48.8566:5000
  &qs=reparer:"smartphone_tablette_et_console"
  &sort=_geo_distance
  &size=10
  &select=nom,adresse,code_postal,ville,horaires_description,site_web,latitude,longitude
```

(URL encodée sur une seule ligne en pratique.)

## Forme de la réponse

```json
{
  "total": 142,
  "next": "...",
  "results": [
    {
      "nom": "Repair Café Elbeuf-sur-Seine",
      "adresse": "14 rue de la République",
      "code_postal": "76500",
      "ville": "Elbeuf",
      "latitude": 49.290368,
      "longitude": 1.001683,
      "horaires_description": "chaque samedi de 9h à 12h",
      "site_web": "https://www.mairie-elbeuf.fr/...",
      "_geopoint": "49.290368,1.001683"
    }
  ]
}
```

## Champs intéressants à retenir

- Identité : `nom`, `siret`, `identifiant`, `paternite`, `type_dacteur`,
  `qualites_et_labels`
- Localisation : `adresse`, `complement_dadresse`, `code_postal`, `ville`,
  `code_commune`, `nom_epci`, `nom_departement`, `nom_region`, `latitude`,
  `longitude`, `_geopoint`
- Contact / horaires : `site_web`, `horaires_description`, `telephone`, `email`
- Activité : une colonne par action (`reparer`, `donner`, `acheter`, …) +
  `propositions_de_services` (JSON détaillé) et `type_de_services`
- Métadonnée : `date_de_derniere_modification`

## Bonnes pratiques

- Toujours utiliser `select` pour limiter la taille de la réponse.
- Ne pas dépasser `size=20` pour une réponse à un utilisateur final.
- En cas de zéro résultat, **élargir le rayon** (× 2, × 4) avant de conclure.
- Mentionner la **paternité** : la valeur du champ `paternite` doit apparaître
  dans la réponse à l'utilisateur (cf. CC-BY).
