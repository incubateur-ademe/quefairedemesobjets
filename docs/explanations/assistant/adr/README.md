# 📐 Décisions d'architecture (ADR)

```{toctree}
:hidden:

0001-pas-de-dsfr.md
0002-geler-noms-tables.md
0003-geojson-plutot-que-html.md
0004-tri-knn-sans-borne-de-distance.md
0005-bboverlaps-pour-la-zone-visible.md
0006-strategie-adaptative-geste-objet.md
```

Format inspiré des [ADR d'aides-agri](https://github.com/betagouv/aides-agri/tree/main/documentation/adr).

Les décisions 0001 à 0003 cadrent le projet, avant toute ligne de code. Les
suivantes consignent des choix d'implémentation contre-intuitifs, chacun
appuyé sur une mesure — et dont deux contredisent le plan initial.

| #                                                | Décision                                              | Statut      |
| ------------------------------------------------ | ----------------------------------------------------- | ----------- |
| [0001](0001-pas-de-dsfr.md)                      | Ne pas utiliser le DSFR dans l'assistant V2           | Proposé     |
| [0002](0002-geler-noms-tables.md)                | Geler les noms de tables lors du renommage des apps   | Proposé     |
| [0003](0003-geojson-plutot-que-html.md)          | Servir la carte en GeoJSON plutôt qu'en HTML          | Proposé     |
| [0004](0004-tri-knn-sans-borne-de-distance.md)   | Trier par l'opérateur KNN, sans borne de distance     | **Accepté** |
| [0005](0005-bboverlaps-pour-la-zone-visible.md)  | Filtrer la zone visible par `bboverlaps`              | **Accepté** |
| [0006](0006-strategie-adaptative-geste-objet.md) | Deux stratégies selon la rareté du couple geste/objet | **Accepté** |

« Proposé » : décidé sur dossier, pas encore éprouvé par du code.
« Accepté » : mis en œuvre, mesuré, couvert par un test de non-régression.
