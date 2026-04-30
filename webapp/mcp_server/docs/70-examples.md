# Exemples concrets

Quelques requêtes complètes, à reproduire telles quelles (les coordonnées
sont des exemples — il faut les obtenir dynamiquement via la BAN).

## Exemple 1 — Réparer un téléphone à Paris

**Question** : « Où réparer mon téléphone à Paris ? »

1. Géocoder « Paris » :

```
GET https://api-adresse.data.gouv.fr/search/?q=paris&limit=1
→ coordonnées [2.3522, 48.8566]
```

2. Chercher les acteurs :

```
GET https://data.ademe.fr/data-fair/api/v1/datasets/wvw1zecq4f4gyvonve5j0hr7/lines
  ?geo_distance=2.3522:48.8566:5000
  &qs=reparer:"smartphone_tablette_et_console"
  &sort=_geo_distance
  &size=10
  &select=nom,adresse,code_postal,ville,horaires_description,site_web,latitude,longitude,paternite
```

## Exemple 2 — Donner des vêtements à Lyon

**Question** : « Où donner mes vieux vêtements à Lyon ? »

```
GET https://data.ademe.fr/data-fair/api/v1/datasets/wvw1zecq4f4gyvonve5j0hr7/lines
  ?geo_distance=4.8357:45.7640:5000
  &qs=donner:"vetement"
  &sort=_geo_distance
  &size=10
```

## Exemple 3 — Jeter un pot de peinture à moitié plein

**Question** : « Où puis-je jeter un pot de peinture à moitié plein près de
Toulouse ? »

C'est un déchet dangereux : utiliser le code
`dechets_de_peintures_vernis_encres_et_colles_produits_chimiques` et
l'action `rapporter`.

```
GET https://data.ademe.fr/data-fair/api/v1/datasets/wvw1zecq4f4gyvonve5j0hr7/lines
  ?geo_distance=1.4442:43.6047:10000
  &qs=rapporter:"dechets_de_peintures_vernis_encres_et_colles_produits_chimiques"
  &sort=_geo_distance
  &size=10
```

## Exemple 4 — Acheter un vélo d'occasion à Bordeaux

**Question** : « Où trouver un vélo d'occasion à Bordeaux ? »

```
GET https://data.ademe.fr/data-fair/api/v1/datasets/wvw1zecq4f4gyvonve5j0hr7/lines
  ?geo_distance=-0.5792:44.8378:5000
  &qs=acheter:"velo"
  &sort=_geo_distance
  &size=10
```

## Exemple 5 — Louer un outil de bricolage à Rennes

**Question** : « Où louer une perceuse à Rennes ? »

```
GET https://data.ademe.fr/data-fair/api/v1/datasets/wvw1zecq4f4gyvonve5j0hr7/lines
  ?geo_distance=-1.6778:48.1173:5000
  &qs=louer:"outil_de_bricolage_et_jardinage"
  &sort=_geo_distance
  &size=10
```

## Exemple 6 — Rapporter des médicaments non utilisés

**Question** : « Comment se débarrasser de médicaments périmés à Marseille ? »

Pour les médicaments, le canal officiel est la **pharmacie** (filière
Cyclamed). On peut tout de même chercher les points enregistrés :

```
GET https://data.ademe.fr/data-fair/api/v1/datasets/wvw1zecq4f4gyvonve5j0hr7/lines
  ?geo_distance=5.3698:43.2965:3000
  &qs=rapporter:"medicaments"
  &sort=_geo_distance
  &size=10
```

## Astuces

- Si zéro résultat, **multiplier le rayon par 2** jusqu'à 50 km, puis
  conclure que rien n'est référencé.
- Toujours réduire la charge utile avec `select=…`.
- Toujours conclure la réponse par : _« Source : Que Faire De Mes Objets et
  Déchets / ADEME »_.
