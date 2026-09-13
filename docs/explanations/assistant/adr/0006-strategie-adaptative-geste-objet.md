# Décision 0006 : deux stratégies selon la rareté du couple geste/objet

Date : 2026-09-13

## Statut

Accepté — mis en œuvre dans `acteur_ids_offering` et
`DisplayedActeurQuerySet.proposing`

## Contexte

Restreindre les lieux à l'objet de la fiche (paramètre `objet`) a fait
apparaître un effet de falaise. Le nombre de lieux concernés par un couple
geste/objet s'étale sur **cinq ordres de grandeur** :

| Couple                        | Lieux en France |
| ----------------------------- | --------------- |
| `reparer` × emballages        | **0**           |
| `vendre_acheter` × emballages | **5**           |
| `trier` × emballages          | **110 320**     |

Le tri KNN ([ADR 0004](0004-tri-knn-sans-borne-de-distance.md)) suppose des
résultats denses : il parcourt l'index du plus proche au plus lointain et
s'arrête au 20ᵉ. Quand il n'y a que 5 correspondances — ou aucune — il
parcourt les 388 000 acteurs sans jamais atteindre son plafond.

Mesures avant correction :

| Couple                                  | Temps        |
| --------------------------------------- | ------------ |
| `reparer` × emballages (0 lieu)         | **3 457 ms** |
| `vendre_acheter` × emballages (5 lieux) | **2 453 ms** |

Deux pistes ont été essayées et écartées :

- **Réintroduire un `ST_DWithin` de 50 km** : 1 036 ms. La borne annule le
  parcours ordonné de l'index sans supprimer le balayage.
- **Une sonde booléenne « ce couple existe-t-il ? »** : corrige le cas à zéro
  lieu (3 457 → 3 ms) mais laisse `vendre_acheter` à 2 453 ms, puisque la
  sonde répond « oui » pour 5 lieux.

## Décision

La stratégie dépend du nombre de lieux concernés, mesuré une fois puis mis en
cache :

```python
SEUIL_PARCOURS_GEOGRAPHIQUE = 1_000

def acteur_ids_offering(groupe_action_code, sous_categorie_ids) -> list[str] | None:
    ...  # None quand le couple dépasse le seuil
```

- **Couple rare** (≤ 1 000 lieux) : la liste des identifiants est établie une
  fois, mise en cache 12 h, et le filtre devient un `identifiant_unique__in`.
  PostgreSQL ne considère plus que ces lieux.
- **Couple courant** (> 1 000 lieux) : la liste n'est pas matérialisée. Le
  parcours géographique trouve ses 20 résultats sans effort, comme avant.

Le seuil de 1 000 est un compromis : assez haut pour que les couples courants
n'entrent jamais dans la branche « liste », assez bas pour que la liste reste
petite à mettre en cache.

La durée de cache est longue (12 h) car un couple geste/objet ne change qu'au
rythme des imports de la data-platform.

## Conséquences

### Positives

- **2 453 ms → 4 ms** sur le pire couple.
- Le cas « aucun lieu ne propose ce geste pour cet objet » coûte 4 ms au lieu
  de 3 457 ms, et c'est un cas courant : beaucoup de gestes n'ont aucun sens
  pour un objet donné.
- Le pire p95, toutes combinaisons zone × geste × objet confondues, passe sous
  les 25 ms pour un budget de 50 ms.

### Négatives

- **Deux chemins de code à maintenir** dans `proposing()`, avec un seuil
  arbitraire. Un couple oscillant autour de 1 000 lieux basculera d'une
  stratégie à l'autre entre deux imports.
- **Le cache peut mentir jusqu'à 12 h** après un import : un lieu nouvellement
  ajouté pour un couple rare n'apparaîtra pas immédiatement. Acceptable pour
  des données qui bougent au rythme des imports, à revoir si la fraîcheur
  devient un enjeu.
- La liste peut atteindre 1 000 identifiants, soit une requête `IN` large.
  Mesurée sans dégradation, mais c'est une borne à surveiller.

### Alternative écartée

**Un index composite ou une vue matérialisée sur (groupe_action,
sous_categorie)** répondrait plus proprement. Écarté ici : les tables
`qfdmo_displayed*` sont reconstruites par la data-platform, et y ajouter un
index unilatéralement sort du périmètre de ce travail. C'est la piste à
privilégier si le seuil devient difficile à régler.

### Garde-fou

```python
def test_lists_candidates_when_the_geste_object_pair_is_rare(self):
    sql = str(...query)
    assert "identifiant_unique" in sql
    assert "EXISTS" not in sql.upper()
```
