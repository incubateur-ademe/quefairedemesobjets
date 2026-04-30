# Géocodage avec l'API BAN

La **Base Adresse Nationale** (BAN) est le service officiel français pour
transformer une adresse en couple `(longitude, latitude)`.

- **Endpoint** : `https://api-adresse.data.gouv.fr/search/`
- **Documentation** : <https://adresse.data.gouv.fr/api-doc/adresse>
- **Coût** : gratuit, sans clé d'API, sous limite de fair-use

## Requête

```http
GET https://api-adresse.data.gouv.fr/search/?q=<adresse>&limit=1
```

Paramètres utiles :

| Paramètre  | Description                                           |
| ---------- | ----------------------------------------------------- |
| `q`        | Adresse libre (rue, ville, code postal, département…) |
| `limit`    | Nombre maximum de résultats (1 à 20)                  |
| `postcode` | Filtrer sur un code postal                            |
| `citycode` | Filtrer sur un code INSEE de commune                  |
| `type`     | `housenumber`, `street`, `locality`, `municipality`   |

## Exemple

```http
GET https://api-adresse.data.gouv.fr/search/?q=10+rue+de+rivoli+paris&limit=1
```

Réponse (extrait) :

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [2.355097, 48.857074] },
      "properties": {
        "label": "10 Rue de Rivoli 75004 Paris",
        "score": 0.97,
        "city": "Paris",
        "postcode": "75004",
        "type": "housenumber"
      }
    }
  ]
}
```

Récupérer `features[0].geometry.coordinates` qui est `[longitude, latitude]`
(dans cet ordre — attention).

## Cas particuliers

- **Ville seule** (ex. `q=Lyon`) → renvoie un point au centre de la commune,
  utilisable pour des recherches dans un rayon de 5–10 km.
- **Code postal seul** (ex. `q=75011`) → centre du quartier, utilisable.
- **Adresse imprécise** → vérifier le `score` ; en dessous de 0.4, demander
  une précision à l'utilisateur.
- **Pas de résultat** → demander à l'utilisateur de reformuler ou de fournir
  une ville/code postal.
