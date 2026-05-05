# Recherche d'acteurs via le tool `search_actors`

Le tool `search_actors` proxy l'API **ADEME data-fair `/lines`** qui expose
chaque acteur du jeu de données comme une ligne JSON filtrable.

- Backend : <https://data.ademe.fr/data-fair/api/v1/datasets/wvw1zecq4f4gyvonve5j0hr7/lines>
- Documentation API : <https://data.ademe.fr/datasets/longue-vie-aux-objets-acteurs-de-leconomie-circulaire/api-doc>
- Coût : gratuit, sans clé d'API
- **Le client MCP n'a jamais à appeler ADEME directement.**

## Schéma d'entrée

| Champ            | Type   | Obligatoire | Description                                                   |
| ---------------- | ------ | ----------- | ------------------------------------------------------------- |
| `longitude`      | number | oui         | Longitude du point de recherche.                              |
| `latitude`       | number | oui         | Latitude du point de recherche.                               |
| `action`         | enum   | oui         | Code d'action — voir `list_actions`.                          |
| `sous_categorie` | string | oui         | Code de sous-catégorie d'objet — voir `list_sous_categories`. |
| `radius_meters`  | int    | non         | Rayon de recherche (100 à 100 000 m, défaut 5000).            |
| `size`           | int    | non         | Nombre maximum d'acteurs (1 à 20, défaut 10).                 |

Ces filtres se traduisent en interne par le filtre data-fair
`qs=<action>:"<sous_categorie>"` plus `geo_distance=<lon>:<lat>:<rayon>` et
`sort=_geo_distance`.

## Schéma de sortie

```json
{
  "total": 142,
  "radius_meters": 5000,
  "action": "reparer",
  "sous_categorie": "smartphone_tablette_et_console",
  "actors": [
    {
      "nom": "Repair Café Elbeuf-sur-Seine",
      "adresse": "14 rue de la République",
      "code_postal": "76500",
      "ville": "Elbeuf",
      "latitude": 49.290368,
      "longitude": 1.001683,
      "horaires_description": "chaque samedi de 9h à 12h",
      "site_web": "https://www.mairie-elbeuf.fr/...",
      "telephone": null,
      "paternite": "Que faire de mes objets et déchets | ADEME | CRAR Normandie",
      "distance_m": 142
    }
  ]
}
```

`distance_m` est calculée par le serveur MCP (formule de Haversine) à partir
des coordonnées de l'acteur et du point de recherche, pour faciliter la
restitution.

## Bonnes pratiques

- En cas de zéro résultat, **élargir le rayon** (×2, ×4) avant de conclure.
  Le tool composé `find_circular_solution` gère cela automatiquement.
- Limiter `size` à 10–20 pour une réponse à un utilisateur final.
- Mentionner la **paternité** : la valeur du champ `paternite` doit apparaître
  dans la réponse à l'utilisateur (cf. licence Etalab / CC-BY).
- Pour enrichir la paternité avec des URLs cliquables, utiliser `list_sources`.
