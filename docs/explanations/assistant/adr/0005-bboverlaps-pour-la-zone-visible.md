# Décision 0005 : filtrer la zone visible par `bboverlaps`, pas `within`

Date : 2026-09-13

## Statut

Accepté — mis en œuvre dans `DisplayedActeurQuerySet.within`

## Contexte

L'exploration de la carte (#3356) envoie la zone visible et attend les lieux
qui s'y trouvent. La carte V1 dispose d'un `in_bbox()` qui filtre par
`location__within=Polygon.from_bbox(bbox)`.

Réutiliser cette méthode donnait un endpoint à **585 ms**, alors que le chemin
par coordonnées tenait en 7 ms. Le geste et le tri n'y étaient pour rien :
`in_bbox()` seul coûtait déjà 578 ms.

Comparaison des opérateurs spatiaux sur la même zone :

| Filtre                 | Temps        |
| ---------------------- | ------------ |
| `location__within`     | **2 080 ms** |
| `location__intersects` | 1,8 ms       |
| `location__bboverlaps` | **1,4 ms**   |

Sur une colonne de type `geography`, `ST_Within` ne peut pas s'appuyer sur
l'index GiST et dégénère en parcours séquentiel. `bboverlaps` utilise
l'opérateur `&&`, que l'index sert directement.

La distinction entre les deux serait significative pour des polygones
(« entièrement contenu » contre « boîtes englobantes qui se recoupent »). Ici
les lieux sont des **points** : pour un point, être dans la boîte et recouper
la boîte sont équivalents.

## Décision

L'assistant définit sa propre méthode plutôt que de réutiliser `in_bbox()` :

```python
def within(self, bbox):
    zone = Polygon.from_bbox(bbox)
    zone.srid = 4326
    centre = Point((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2, srid=4326)
    return (
        self.physical()
        .filter(location__bboverlaps=zone)
        .order_by(NearestTo("location", centre))
    )
```

`in_bbox()` de la V1 **n'est pas modifiée** : elle est utilisée par la carte
existante, dont les performances et le comportement ne sont pas dans le
périmètre de ce travail.

## Conséquences

### Positives

- **585 ms → 5,6 ms** sur l'endpoint complet, soit un facteur 100.
- Le tri par proximité au centre de la zone, exigé par #3356, est conservé.
- Aucune modification du code de la carte V1, donc aucun risque de régression
  sur l'existant.

### Négatives

- **Deux méthodes de filtrage par zone coexistent** dans le même QuerySet :
  `in_bbox()` (V1) et `within()` (assistant). Un développeur peut choisir la
  mauvaise. Le nom et la docstring de `within()` expliquent la différence.
- `bboverlaps` serait **incorrect pour des géométries non ponctuelles**. Si un
  jour des lieux étaient représentés par des polygones (une zone de collecte,
  par exemple), il faudrait revenir à `intersects`, qui reste rapide (1,8 ms).

### Neutres

- La V1 gagnerait probablement à la même correction. Ce n'est pas fait ici
  faute de mandat, mais c'est une piste d'optimisation documentée.

### Garde-fou

```python
def test_within_uses_the_indexed_bounding_box_operator(self):
    sql = str(...query)
    assert "&&" in sql
    assert "ST_Within" not in sql
```
