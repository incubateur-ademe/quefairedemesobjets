# Suggestions review API

## Overview

The `/api/suggestions/` router serves the review screen of the SOURCE
suggestions (see [the screen](../webapp/revue-suggestions.md)). It is reserved to
**superusers**:

- authentication by the Django session; anonymous requests get `401`;
- authenticated users who are not superusers get `403`;
- unsafe methods (`POST`, `PUT`, `DELETE`) require the CSRF token in the
  `X-CSRFToken` header (cookie `csrftoken`, set by the page `/data/revue/`).

The OpenAPI schema is published on `/api/openapi.json` (documentation on
`/api/docs`, tag « Revue suggestions »).

## Conventions

- Paginated lists answer `{ items, total, page, page_size }`, `page` starting at 1.
- Errors answer `{ code, detail, errors?, current? }`:

| Status | Meaning                                                                                                                            |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| `401`  | Not authenticated                                                                                                                  |
| `403`  | Not a superuser, or invalid CSRF token                                                                                             |
| `404`  | Unknown resource, or cohorte which is not SOURCE                                                                                   |
| `409`  | Conflict: the groupe changed meanwhile (`expected_modifie_le`), or its statut forbids the action. `current` is the current groupe. |
| `422`  | Invalid input: filter, value refused by the validation of the model (`errors` by field), action forbidden by the review policy     |
| `502`  | Annuaire des entreprises unavailable                                                                                               |

## Routes

### Cohortes

| Route                            | Description                                                                                                                                                    |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /cohortes`                  | SOURCE cohortes having groupes. Params: `filtre`, `type_action[]`, `statut[]`, `cree_apres`, `cree_avant`, `tri` (ex: `-cree_le`), `page`, `page_size` (≤ 200) |
| `GET /cohortes/filtres`          | Filterable fields of the cohortes (with the keys of `metadata`)                                                                                                |
| `GET /cohortes/{id}`             | A cohorte, its counters and its review policy                                                                                                                  |
| `GET /cohortes/{id}/logs`        | Its `SuggestionLog`, the most severe first. Params: `niveau[]`, `page`, `page_size`                                                                            |
| `GET /cohortes/{id}/logs/export` | Same, as an Excel file                                                                                                                                         |

### Review of a cohorte

| Route                              | Description                                                                                                                                     |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /cohortes/{id}/revue/filtres` | Filterable fields of the groupes and lignes (with the keys of `contexte`, the tuples, the reviewers)                                            |
| `GET /cohortes/{id}/groupes`       | Page of groupes, with their lignes. Params: `filtre`, `tuples[]` (`champ,champ`), `afficher` (`avalider` / `tout`), `page`, `page_size` (≤ 200) |
| `GET /cohortes/{id}/lignes`        | Page of lignes: references `{ groupe_id, key }` and their groupes. Same params, `page_size` ≤ 1000                                              |
| `GET /cohortes/{id}/stats`         | Counters of the unit of the view (`vue`), size of each view, counts per tuple                                                                   |
| `GET /groupes/{id}`                | Detail of a groupe: acteur displayed, map points, SIRET / SIREN with their source                                                               |
| `GET /annuaire-entreprises`        | Entreprise and établissement of a SIRET / SIREN (`champ`, `valeur`), from the public API « Recherche d'entreprises », cached one day            |

A ligne is identified by its key `"<groupe id>:<champ>,<champ>"`.

### Writes on a groupe

Each write takes `expected_modifie_le` (the `modifie_le` of the groupe read by the
client) and answers the updated groupe.

| Route                                | Body                                                                                                    |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| `POST /groupes/{id}/decision`        | `{ action: "validate" \| "reject" \| "resubmit" }`                                                      |
| `POST /groupes/{id}/lignes/decision` | `{ champs: [[champ, …], …], action: "validate" \| "resubmit" }`                                         |
| `PUT /groupes/{id}/propositions`     | `{ suggestion_modele: "RevisionActeur" \| "ParentRevisionActeur", champs, valeurs: { champ: valeur } }` |
| `DELETE /groupes/{id}/propositions`  | Params `suggestion_modele`, `champs[]`                                                                  |
| `POST /groupes/{id}/report`          | `{ cible: "correction" \| "parent", champs?: [[…]] }` (all the reportable lignes when absent)           |

### Mass actions

| Route                                | Description                                                                                                                       |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| `POST /cohortes/{id}/actions/apercu` | Number of elements each action would really change on a selection                                                                 |
| `POST /cohortes/{id}/actions`        | Runs `{ vue, action, selection }`. `200 { affected, skipped }`, or `202 { job_id, total }` for a report of more than 1000 groupes |
| `GET /jobs/{job_id}`                 | State of a background report: `pending`, `running`, `done`, `error`                                                               |

A selection is either the checked elements, or all the elements matching the
filter except some, the server applying the filter again:

```json
{ "vue": "groupes", "selection": { "mode": "ids", "ids": [12, 13] } }
```

```json
{
  "vue": "lignes",
  "selection": {
    "mode": "filtre",
    "filtre": "{\"op\":\"and\",\"conditions\":[]}",
    "tuples": ["latitude,longitude"],
    "afficher": "avalider",
    "exclus": ["12:latitude,longitude"]
  }
}
```

Actions: `validate`, `reject` (view `groupes` only), `resubmit`,
`report_correction`, `report_parent`.

## Structured filters

No DjangoQL and no regex: the client sends a JSON tree, in the `filtre` query
parameter.

```json
{
  "op": "and",
  "conditions": [
    { "field": "groupe.statut", "operator": "eq", "value": "AVALIDER" },
    {
      "op": "or",
      "conditions": [
        { "field": "ligne.champ", "operator": "eq", "value": "url" },
        {
          "field": "contexte.source_code",
          "operator": "icontains",
          "value": "eco"
        }
      ]
    }
  ]
}
```

- At most 3 levels and 30 conditions.
- Fields come from a server-side whitelist, described with their type, label,
  operators and choices by the `…/filtres` routes. JSON fields are addressed by a
  key path (`metadata.<key>`, `contexte.<key>`).
- Operators by type:

| Type             | Operators                                                                      |
| ---------------- | ------------------------------------------------------------------------------ |
| `text`           | `eq`, `neq`, `icontains`, `startswith`, `in`, `is_empty`, `is_not_empty`       |
| `number`, `date` | `eq`, `neq`, `in` (numbers), `gt`, `lt`, `between`, `is_empty`, `is_not_empty` |
| `bool`           | `eq`                                                                           |
| `choice`         | `eq`, `neq`, `in`                                                              |
| `user`           | `eq`, `in`, `is_empty`, `is_not_empty`                                         |

- Text comparisons ignore case and accents (`unaccent`).
- In the view Groupes, a condition on the ligne keeps the groupes having **at
  least one** ligne matching it (two conditions joined by `and` may match two
  different lignes). In the view Lignes, a condition on the groupe applies to the
  groupe of the ligne.

## Testing

`webapp/integration_tests/revue/` covers the routes (authentication, filters,
pagination, writes, conflicts, mass actions), on the dataset of the command
`seed_revue_suggestions`.
