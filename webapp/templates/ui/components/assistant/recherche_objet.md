# Recherche d'objet

Combobox avec suggestions, pour saisir l'objet ou le déchet dont on veut se
défaire.

## Comment l'utiliser

```django
{% include "ui/components/assistant/recherche_objet.html" %}
```

| Paramètre     | Requis | Rôle                          |
| ------------- | ------ | ----------------------------- |
| `id`          | ⚪️     | préfixe des identifiants ARIA |
| `label`       | ⚪️     | libellé du champ              |
| `placeholder` | ⚪️     | exemple de saisie             |

Le composant émet `assistant-combobox:chosen` avec `{ label, slug }` quand
l'usager retient une suggestion.

## Endpoint

`GET /api/v1/objets?q=chaise` renvoie du JSON, le client construit sa liste :

```json
{ "results": [{ "label": "Chaise", "slug": "meubles" }] }
```

La liste s'ouvre à partir de deux caractères, jamais au focus. Côté serveur,
un `statement_timeout` de 300 ms rend une liste vide plutôt que de figer le
champ.

## Accessibilité

Patron W3C APG _combobox-autocomplete-list_ :

| Élément | Rôle ARIA                                                                    |
| ------- | ---------------------------------------------------------------------------- |
| `input` | `role="combobox"`, `aria-expanded`, `aria-controls`, `aria-activedescendant` |
| `ul`    | `role="listbox"`                                                             |
| `li`    | `role="option"`, `aria-selected`                                             |

Clavier : `↓`/`↑` parcourent les suggestions en boucle, `Entrée` retient la
suggestion active, `Échap` referme la liste. Le nombre de suggestions est
annoncé dans une région `role="status"` présente dès le chargement.
