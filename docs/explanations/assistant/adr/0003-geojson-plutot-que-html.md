# Décision 0003 : servir la carte en GeoJSON plutôt qu'en HTML

Date : 2026-09-12

## Statut

Proposé

## Contexte

La carte V1 reçoit du **HTML** : le serveur rend un `<a data-controller="pinpoint">`
par acteur dans un Turbo Frame, et MapLibre attache ces éléments comme
marqueurs. C'est simple et ça fonctionne pour un affichage où chaque recherche
repart de zéro.

La spec de l'assistant V2
([#3356](https://app.notion.com/p/3a06523d57d780589476d537f8776008)) impose un
comportement différent :

> « chaque point reste affiché tant que son emplacement reste visible à
> l'écran. Concrètement, si l'usager dézoome ou déplace légèrement la carte
> sans faire sortir un lieu du cadre, ce lieu ne bouge pas et ne disparaît
> pas. »

> « quand l'usager dézoome trop loin […] les points ne sont pas perdus : ils
> sont seulement mis de côté. Si l'usager rezoome ensuite à peu près au niveau
> où il était, il retrouve exactement les mêmes lieux qu'avant, **sans que la
> carte n'aille en chercher de nouveaux**. »

Ces deux règles supposent que **le client possède l'état des marqueurs** : il
doit pouvoir comparer l'ancien et le nouvel ensemble, décider lesquels
conserver, et restituer un ensemble précédent sans requête.

Avec une réponse HTML, le serveur réécrit l'intégralité des marqueurs à chaque
rafraîchissement : le client n'a aucun moyen de distinguer « ce point est le
même qu'avant » de « ce point est nouveau », ni de conserver un ensemble mis de
côté.

Le ticket [#3432](https://app.notion.com/p/3d86523d57d78018a4c9c685280d0fae)
acte ce changement de contrat.

## Décision

L'endpoint `/assistant/lieux.geojson` renvoie une **FeatureCollection GeoJSON**.
Le contrôleur Stimulus possède l'état (`Map<uuid, feature>`), applique les
règles de fusion et de plafond, et dessine les marqueurs.

La sérialisation vit sur le QuerySet (`en_geojson()`), la vue ne fait que
traduire les paramètres de requête en appel manager.

## Conséquences

### Positives

- Les deux règles de persistance de #3356 deviennent **implémentables**.
- Charge utile plus légère : ~120 octets par lieu en JSON contre ~400 en HTML
  avec attributs Stimulus.
- L'endpoint devient **cacheable par HTTP** (`cache_control` +
  `stale_while_revalidate`), sans fabriquer de clé applicative.
- Le contrat est testable sans navigateur : on teste le JSON, pas du HTML.
- Un format standard, réutilisable par d'autres consommateurs si besoin.

### Négatives

- **Le rendu des marqueurs passe côté client** : plus de logique JavaScript à
  écrire et à tester qu'avec du HTML rendu par Django.
- Deux chemins de rendu coexistent dans le projet (HTML pour la carte V1,
  GeoJSON pour l'assistant V2) tant que la V1 n'est pas migrée.
- L'accessibilité doit être traitée explicitement : un GeoJSON n'est pas du
  DOM, donc une liste accessible des lieux est **obligatoire** en parallèle
  (voir [04-stimulus](../04-stimulus.md), section « Accessibilité de la carte »).

### Neutres

- Le contrat GeoJSON est documenté dans `assistant/README.md` ; il devra être
  versionné si un consommateur externe s'y branche.
