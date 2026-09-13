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

Le composant émet `assistant-recherche-objet:choisi` avec
`{ libelle, slug }` quand l'usager retient une suggestion.

## Endpoint dédié

`GET /assistant/recherche/objet?q=chaise` renvoie du **JSON**, pas du HTML :

```json
{ "resultats": [{ "libelle": "Chaise", "slug": "meubles" }] }
```

Le gabarit HTML du moteur historique coûtait plus cher que la requête
elle-même — environ 25 ms de rendu pour 15 ms de SQL. Le client construit sa
propre liste, ce qui divise le temps de réponse par deux.

| Mesure (HTTPS, 10 requêtes) | p95   |
| --------------------------- | ----- |
| `q=cha`                     | 23 ms |
| `q=chaise`                  | 21 ms |
| `q=telephone`               | 20 ms |
| `q=velo`                    | 20 ms |

Budget : 50 ms.

## Périmètre MVP

La liste ne s'ouvre **qu'à partir de deux caractères saisis**, jamais au focus.
C'est une exclusion explicite du MVP ([#3295](https://app.notion.com/p/38e6523d57d780049d61e54dc439c1f3)) :
« pas de liste qui s'ouvre directement ».

## Accessibilité

Le composant suit le patron W3C APG _combobox-autocomplete-list_ :

| Élément | Rôle ARIA                                                                    |
| ------- | ---------------------------------------------------------------------------- |
| `input` | `role="combobox"`, `aria-expanded`, `aria-controls`, `aria-activedescendant` |
| `ul`    | `role="listbox"`                                                             |
| `li`    | `role="option"`, `aria-selected`                                             |

Clavier : `↓`/`↑` parcourent les suggestions en boucle, `Entrée` retient la
suggestion active, `Échap` referme la liste.

Le nombre de suggestions est annoncé dans une région `role="status"` présente
dès le chargement — injectée après coup, elle ne serait pas lue par certains
lecteurs d'écran.

## Points d'attention

### Requêtes annulables

Chaque frappe annule la requête précédente via `AbortController`. Sans cela,
une réponse lente arrivant après une réponse récente réafficherait des
suggestions périmées pendant que l'usager continue de taper.

### Débounce de 150 ms

`static debounces = [{ name: "chercher", wait: 150 }]`. Assez court pour rester
imperceptible, assez long pour ne pas émettre une requête par caractère.

### Garde-fou côté serveur

La vue pose un `statement_timeout` de 300 ms. Une recherche pathologique rend
une liste vide plutôt que de figer le champ de saisie.
