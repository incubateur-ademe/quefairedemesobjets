# Géocodage via le tool `geocode_address`

Le tool `geocode_address` proxy la **Base Adresse Nationale** (BAN), service
officiel français pour transformer une adresse en `(longitude, latitude)`.

- Backend : <https://api-adresse.data.gouv.fr/search/>
- Documentation BAN : <https://adresse.data.gouv.fr/api-doc/adresse>
- Coût : gratuit, sans clé d'API, sous limite de fair-use
- **Le client MCP n'a jamais à appeler la BAN directement.**

## Schéma d'entrée

| Champ   | Type   | Obligatoire | Description                                     |
| ------- | ------ | ----------- | ----------------------------------------------- |
| `query` | string | oui         | Adresse libre, ville, code postal, département. |
| `limit` | int    | non         | Nombre maximum de résultats (1 à 10, défaut 1). |

## Schéma de sortie

```json
{
  "query": "10 rue de Rivoli Paris",
  "results": [
    {
      "longitude": 2.355097,
      "latitude": 48.857074,
      "label": "10 Rue de Rivoli 75004 Paris",
      "score": 0.97,
      "city": "Paris",
      "postcode": "75004",
      "type": "housenumber"
    }
  ]
}
```

## Cas particuliers

- **Ville seule** (ex. `Lyon`) → renvoie un point au centre de la commune,
  utilisable pour des recherches dans un rayon de 5–10 km.
- **Code postal seul** (ex. `75011`) → centre du quartier, utilisable.
- **Adresse imprécise** → vérifier `score` ; en dessous de 0.4, demander une
  précision à l'utilisateur.
- **Pas de résultat** (`results == []`) → demander à l'utilisateur de
  reformuler ou de fournir une ville/code postal.

## Note

Le tool composé `find_circular_solution` appelle déjà `geocode_address` en
interne. N'appelle `geocode_address` séparément que si tu as besoin des
coordonnées en dehors d'une recherche d'acteurs (ex. pour une autre tool).
