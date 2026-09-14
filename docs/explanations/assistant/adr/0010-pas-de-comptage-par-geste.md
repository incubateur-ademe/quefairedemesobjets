# Décision 0010 : ne pas compter les solutions par geste

Date : 2026-09-14

## Statut

Accepté — répond à la question laissée ouverte par #3295 et par la PR 9.

## Contexte

La spec #3295 classe le compteur par geste — « Nb de solutions à proximité par
geste indiqué dans le bouton » — en ❌, avec une réserve :

> Possible de prendre ce sujet dans le cadre du MVP uniquement si ça passe.
> **À évaluer techniquement côté dev.**

Cette ADR est cette évaluation.

## Mesure

Compter les lieux d'un geste, c'est exécuter la requête de la carte sans en
lire les résultats. Mesuré sur la base de développement (388 000 acteurs),
médiane de cinq exécutions, pour les vingt lieux les plus proches :

| Objet        | Zone  | Total des 5 gestes |
| ------------ | ----- | ------------------ |
| `meubles`    | Paris | **575 ms**         |
| `meubles`    | Auray | **413 ms**         |
| `emballages` | Paris | 23 ms              |
| `emballages` | Auray | 27 ms              |

Le détail par geste, à Paris sur `meubles` :

| Geste                       | Médiane |
| --------------------------- | ------- |
| `donner_echanger_rapporter` | 198 ms  |
| `trier`                     | 173 ms  |
| `vendre_acheter`            | 122 ms  |
| `reparer`                   | 79 ms   |
| `emprunter_preter_louer`    | 3 ms    |

Le budget de la fiche est de **50 ms**. `meubles` le dépasse d'un facteur
**onze**, et c'est une fiche ordinaire, pas un cas limite.

### L'écart est le vrai problème

`emballages` coûte 23 ms, `meubles` 575 ms : un rapport de 25 entre deux fiches
du même site. Un compteur qui rend la page instantanée sur certains objets et
inutilisable sur d'autres est pire qu'un compteur absent — l'usager attribue la
lenteur au produit, pas à la richesse du catalogue.

### L'alternative groupée ne sauve rien

Une seule requête agrégée par groupe d'action, testée :

```python
DisplayedPropositionService.objects
    .filter(sous_categories__id__in=ids)
    .values_list("action__groupe_action__code")
    .annotate(n=Count("acteur_id", distinct=True))
```

**140 ms, et sans aucune contrainte géographique.** Elle compte les lieux de
toute la France, ce qui ne répond pas à la question posée — « combien de
solutions près de moi ». Ajouter la proximité la ramènerait au niveau des cinq
requêtes séparées, le regroupement n'économisant que le trajet réseau.

## Décision

**Pas de compteur par geste dans le MVP.** Le bouton garde son libellé fixe,
« Je découvre les solutions », comme le prévoit la maquette.

## Ce qui rendrait la décision réversible

Le coût vient de la jointure entre propositions de service et sous-catégories,
pas du tri géographique ([ADR 0004](0004-tri-knn-sans-borne-de-distance.md) l'a
déjà ramené à 2 ms). Deux pistes, si le produit y tient :

1. **Un agrégat pré-calculé** (nombre de lieux par maille × geste × catégorie),
   côté data-platform. La maille EPCI existe déjà — voir la discussion en
   [ADR 0009 Q3](0009-questions-a-trancher.md), qui bute sur la même donnée.
2. **Un compteur approché**, chargé après la page et affiché quand il arrive.
   La fiche resterait rapide, au prix d'un chiffre qui apparaît en différé.

Aucune des deux n'est du ressort du MVP : la première demande un pipeline, la
seconde un compromis d'affichage à valider avec le design.

## Conséquences

- La fiche objet tient son budget : aucune requête d'acteurs à son rendu.
- Le compteur global (« 239 solutions trouvées ») était déjà écarté par #3295 ;
  cette décision ne fait qu'étendre le même raisonnement au détail par geste.
- **Le chiffre manque à l'usager** : rien n'indique qu'un geste n'a aucune
  solution à proximité avant d'ouvrir la carte. C'est le coût assumé, atténué
  par le fait que la carte, elle, affiche un message clair quand elle ne trouve
  rien.
