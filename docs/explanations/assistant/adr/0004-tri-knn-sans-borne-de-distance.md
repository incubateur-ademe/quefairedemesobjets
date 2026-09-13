# Décision 0004 : trier par l'opérateur KNN, sans borne de distance

Date : 2026-09-13

## Statut

Accepté — mis en œuvre dans `DisplayedActeurQuerySet.nearest_to`

Remplace la stratégie « rayon croissant » décrite dans
[05-données et cache](../05-donnees-et-cache.md), écrite avant toute mesure.

## Contexte

La spec #3356 impose au plus 20 lieux, triés par distance. Le plan prévoyait
d'y parvenir par des paliers de rayon croissants (2 km → 5 km → 20 km), sur la
base d'une mesure montrant 450 ms à 20 km contre 21 ms à 2 km.

Confrontée à la base réelle (388 000 acteurs), cette approche ne tient pas :

| Rayon | Temps  |
| ----- | ------ |
| 20 km | 737 ms |
| 5 km  | 154 ms |
| 2 km  | 10 ms  |

Le budget est de 50 ms. Or un palier de 5 km le dépasse déjà, et les paliers
sont nécessaires en zone rurale où 20 lieux ne tiennent pas dans 2 km. Chaque
palier infructueux ajoute par ailleurs une requête.

`EXPLAIN ANALYZE` montre la cause : `ST_DWithin` empêche PostgreSQL de
parcourir l'index GiST dans l'ordre des distances. Il charge **tous** les
candidats du rayon, calcule leur distance, les trie, puis applique le `LIMIT`.
À 5 km autour de Paris, cela fait 4 141 lignes chargées pour en renvoyer 20.

## Décision

On **supprime toute borne de distance** et on trie par l'opérateur KNN `<->`
de PostGIS :

```python
def nearest_to(self, longitude, latitude):
    reference_point = Point(float(longitude), float(latitude), srid=4326)
    return self.physical().order_by(NearestTo("location", reference_point))
```

`NearestTo` (`qfdmo/geo_expressions.py`) est une expression `Func` produisant
`location <-> point::geography`. L'ORM Django n'exprime pas nativement cet
opérateur.

PostgreSQL parcourt alors l'index GiST du plus proche au plus lointain et
s'arrête au 20ᵉ résultat. Le plafond de résultats borne le travail ; le rayon
devient inutile.

## Conséquences

### Positives

- **Deux ordres de grandeur gagnés** : 2 ms contre 437 ms à Paris.
- Une seule requête, quelle que soit la densité de la zone.
- Le comportement est uniforme entre ville et campagne : 2,2 ms à Paris,
  1,7 ms en Savoie rurale.
- Le code est plus court : ni paliers, ni `count()` intermédiaire.

### Négatives

- **La distance renvoyée par `<->` est approchée** : elle sert au tri, jamais à
  l'affichage. Afficher une distance exacte demanderait d'annoter `Distance`
  en parallèle, ce que le MVP ne fait pas.
- **Aucune limite géographique** : si un geste n'est proposé nulle part à
  proximité, la requête renvoie les 20 lieux les plus proches même à 300 km.
  C'est acceptable ici car la carte se cadre sur les résultats, mais ce n'est
  pas un filtre de pertinence. Voir [ADR 0006](0006-strategie-adaptative-geste-objet.md)
  pour le cas dégénéré où ces lieux n'existent pas.
- Une expression SQL maison à maintenir, non couverte par l'ORM.

### Garde-fou

```python
def test_nearest_to_does_not_bound_the_search(self):
    sql = str(...query)
    assert "ST_DWithin" not in sql
    assert "<->" in sql
```

Un refactor réintroduisant une borne ferait chuter les performances sans
erreur visible : ce test l'empêche.
