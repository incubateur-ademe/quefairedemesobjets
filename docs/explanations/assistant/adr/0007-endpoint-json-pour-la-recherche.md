# Décision 0007 : servir la recherche d'objet en JSON, pas en HTML

Date : 2026-09-13

## Statut

Accepté — mis en œuvre dans `assistant/views/recherche.py`

Remplace la stratégie « sous-classer `AutocompleteHomeSearchView` » décrite
dans [02-architecture](../02-architecture.md) et
[06-découpage PR](../06-decoupage-pr.md), écrite avant mesure.

## Contexte

Le plan prévoyait de réutiliser la recherche existante en n'en changeant que le
gabarit :

```python
class AutocompleteObjetView(AutocompleteHomeSearchView):
    template_name = "ui/components/assistant/_partials/resultats_objet.html"
```

Mesuré sur l'endpoint historique : médiane 36-49 ms, **p95 jusqu'à 69 ms**,
pour un budget de 50 ms et une interaction qui doit sembler instantanée.

Le profilage sépare nettement les deux coûts :

| Étape                                           | Temps      |
| ----------------------------------------------- | ---------- |
| Requête `Fuzzy(unaccent=True)` sur 2 271 termes | **15 ms**  |
| Rendu du gabarit HTML + middlewares             | **~25 ms** |

Le rendu coûtait donc plus cher que la recherche elle-même, pour produire un
fragment que le client sait construire seul.

## Décision

Un endpoint dédié renvoyant du JSON :

```text
GET /assistant/recherche/objet?q=chaise
{ "resultats": [{ "libelle": "Chaise", "slug": "meubles" }] }
```

La vue reste mince : elle valide la saisie, délègue à `SearchTerm`, et
sérialise. Elle pose par ailleurs un `statement_timeout` de 300 ms — une
recherche pathologique doit rendre une liste vide, jamais figer la saisie.

## Le piège du N+1

`SearchTerm` est une classe de base : seules ses sous-classes savent produire
un titre. Passer par `terme.specific` donne les bons libellés mais interroge
chaque sous-classe l'une après l'autre, soit **30 requêtes pour 7 résultats**.

La résolution groupée ramène cela à trois requêtes, quel que soit le nombre de
suggestions :

```python
for modele in (ProduitPageSearchTerm, SearchTag, Synonyme):
    manquants = [id for id in ids if id not in resolus]
    ...
```

> ⚠️ Sans cette résolution, les libellés sortent **vides** : c'est le bug qui a
> été observé avant correction, et qui ne se voit qu'en regardant la réponse.

## Conséquences

### Positives

- **p95 de 20-48 ms** contre 69 ms auparavant, mesuré en HTTPS sur cinq
  requêtes différentes.
- 18 requêtes SQL par appel au lieu de 30.
- Le client construit sa liste : il maîtrise l'ARIA, la navigation clavier et
  l'état actif sans dépendre d'un fragment serveur.
- Le contrat JSON est testable sans navigateur.

### Négatives

- **Deux chemins de recherche coexistent** : l'endpoint historique (HTML, pour
  l'assistant V1) et celui-ci. Une évolution du moteur devra toucher les deux.
- Le rendu des suggestions passe côté client, donc il ne fonctionne pas sans
  JavaScript. Acceptable ici : le champ reste utilisable et la soumission mène
  à la fiche, mais c'est une dépendance de plus.
- `emballage` mesure **48 ms p95**, proche du budget. À surveiller : si le
  corpus grossit, la piste suivante est un index trigramme dédié plutôt qu'une
  optimisation applicative.

### Alternative écartée

**Garder le gabarit HTML et alléger le rendu** : le fragment reste soumis aux
middlewares et au moteur de templates. Le gain plafonnait bien au-dessus du
coût de la requête, pour un contrat plus rigide côté client.
