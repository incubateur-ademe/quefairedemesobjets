# API Statistiques publiques

## Présentation

L'endpoint `/api/stats` permet de récupérer les statistiques publiques sur les **visiteurs orientés** : visiteurs ayant consulté une page d'un produit ou ayant fait une recherche sur la carte.

Les données sont agrégées depuis PostHog selon la périodicité demandée.

## Endpoint

```
GET /api/stats
```

## Paramètres de requête

| Paramètre     | Type    | Requis | Valeur par défaut | Description                                                                               |
| ------------- | ------- | ------ | ----------------- | ----------------------------------------------------------------------------------------- |
| `periodicity` | string  | Non    | `month`           | Granularité de regroupement des KPI. Valeurs possibles : `day`, `week`, `month`, `year`   |
| `since`       | integer | Non    | `null`            | Nombre d'itérations de la période souhaitée (ex: `30` pour 30 jours si `periodicity=day`) |

## Exemples de requêtes

### Statistiques mensuelles (par défaut)

```bash
GET /api/stats
```

### Statistiques des 30 derniers jours

```bash
GET /api/stats?periodicity=day&since=30
```

### Statistiques des 12 derniers mois

```bash
GET /api/stats?periodicity=month&since=12
```

### Statistiques des 4 dernières semaines

```bash
GET /api/stats?periodicity=week&since=4
```

## Réponse

### Format

```json
{
  "description": "Visiteurs orientés : visiteurs ayant consultés une page d'un produit ou ayant fait une recherche sur la carte",
  "stats": [
    {
      "date": 1704067200,
      "iso_date": "2024-01-01T00:00:00+00:00",
      "value": 1234
    },
    {
      "date": 1704153600,
      "iso_date": "2024-01-02T00:00:00+00:00",
      "value": 1456
    }
  ]
}
```

### Champs de réponse

| Champ              | Type    | Description                                            |
| ------------------ | ------- | ------------------------------------------------------ |
| `description`      | string  | Description de la métrique retournée                   |
| `stats`            | array   | Liste des points de données, triés par date croissante |
| `stats[].date`     | integer | Timestamp Unix (secondes) du début de la période       |
| `stats[].iso_date` | string  | Date ISO 8601 du début de la période (UTC)             |
| `stats[].value`    | float   | Nombre de visiteurs orientés pour cette période        |

## Documentation interactive

Cette route API est testable sur `/api/docs` qui fournit une interface Swagger/OpenAPI interactive permettant de tester l'endpoint directement depuis le navigateur.

## Notes techniques

- Les données sont récupérées depuis PostHog via l'API Query
- Les dates sont normalisées au début de la période demandée (ex: début du mois pour `month`)
- En cas d'erreur de communication avec PostHog, l'API retourne une erreur HTTP 502
- Le paramètre `since` permet de limiter la période de données retournées (ex: `since=30` avec `periodicity=day` retourne les 30 derniers jours)
