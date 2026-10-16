# Carte de l'assistant

Carte MapLibre affichant au plus 20 lieux proposant un geste, mise à jour
pendant l'exploration.

## Comment l'utiliser

```django
{% include "ui/components/assistant/carte.html" with
   geste="reparer"
   fiche="telephone-mobile"
   longitude=2.3488
   latitude=48.8534
   adresse_precise=True
   couleur_geste="#009081"
   parametres_lieu="geste=reparer&fiche=telephone-mobile"
   lieux=lieux %}
```

| Paramètre         | Requis | Rôle                                                                 |
| ----------------- | ------ | -------------------------------------------------------------------- |
| `geste`           | ✅     | code d'un `GroupeAction` — voir ci-dessous                           |
| `longitude`       | ✅     | centre initial                                                       |
| `latitude`        | ✅     | centre initial                                                       |
| `couleur_geste`   | ✅     | couleur des pinpoints, issue de `GroupeAction.couleur`               |
| `fiche`           | ⚪️     | slug d'une fiche, restreint les lieux à ses sous-catégories          |
| `adresse_precise` | ⚪️     | affiche la punaise rouge (#3356 §4) ; jamais pour une commune        |
| `parametres_lieu` | ⚪️     | query string ajoutée au lien de chaque punaise vers `assistant:lieu` |
| `lieux`           | ⚪️     | liste rendue côté serveur pour la version accessible                 |
| `debug`           | ⚪️     | affiche l'overlay de durée des requêtes (`chrono_controller`)        |

> ⚠️ `geste` attend un code de **`GroupeAction`** (`reparer`,
> `donner_echanger_rapporter`, `emprunter_preter_louer`, `vendre_acheter`,
> `trier`) et non d'`Action`. Un `geste="deposer"` ne correspond à rien : le
> code attendu est `trier`.

## Découpage du code

Trois fichiers, chacun avec une responsabilité unique. Le découpage suit la
logique d'un composant React : une couche de données pure, une couche de rendu,
un contrôleur qui orchestre.

```
js/assistant/visible_places.ts   logique pure, testée sans navigateur
js/assistant/pinpoint.ts         fabrication des éléments DOM
controllers/assistant/carte_controller.ts   cycle de vie et requêtes
```

| Fichier             | Responsabilité                                         | Ne fait pas                     |
| ------------------- | ------------------------------------------------------ | ------------------------------- |
| `visible_places.ts` | fusion, filtrage par zone, plafond de 20               | aucun accès au DOM ni au réseau |
| `pinpoint.ts`       | élément DOM d'un marqueur, couleur, libellé accessible | ne connaît pas la carte         |
| `carte_controller`  | MapLibre, `fetch`, annonces, nettoyage                 | ne calcule aucune règle métier  |

La logique métier vit dans `visible_places.ts`, sans dépendance au navigateur :
elle se teste en Jest (`visible_places.test.ts`), sans monter de carte.

## Les règles métier implémentées

Toutes viennent de la spec
[#3356](https://app.notion.com/p/3a06523d57d780589476d537f8776008).

### Rafraîchissement après une seconde d'immobilité

```typescript
static debounces = [{ name: "refresh", wait: SETTLE_DELAY_MS }]
```

Rien ne se passe pendant que l'usager déplace ou zoome. `useDebounce` de
`stimulus-use` applique les défauts `leading: false, trailing: true`, soit
exactement « attendre que ça s'arrête ».

### Un point visible ne disparaît pas

C'est la règle la plus subtile, et la raison pour laquelle l'endpoint renvoie
du GeoJSON plutôt que du HTML : le client doit posséder l'état des marqueurs
pour comparer l'ancien et le nouveau.

```typescript
const kept = shown.filter((place) => isInArea(place, area))
const merged = new Map(kept.map((place) => [place.uuid, place]))
for (const place of incoming) {
  if (merged.size >= cap) break
  merged.set(place.uuid, place)
}
```

Les lieux conservés sont insérés **en premier** : ce sont eux qui remplissent
le plafond de 20. Un lieu sous les yeux de l'usager ne saute donc jamais, ce
qui répond à un retour de test explicite.

### Dézoom : masqués, pas perdus

Sous le zoom d'un département, les marqueurs sont retirés de la carte mais
`this.places` est conservé. Un rezoom les réaffiche **sans requête**.

### Requêtes annulables

```typescript
this.pendingRequest?.abort()
this.pendingRequest = new AbortController()
```

Sans cela, une réponse lente arrivant après une réponse récente repeindrait une
zone déjà quittée. Un usager qui balaie la carte enchaîne les rafraîchissements :
le scintillement serait visible.

## Points d'attention

### `disconnect()` est obligatoire

```typescript
disconnect() {
  this.pendingRequest?.abort()
  this.markers.forEach((marker) => marker.remove())
  this.map?.remove()
}
```

Sans `carte.remove()`, le contexte WebGL fuit à chaque navigation de Turbo
Frame. Le problème a déjà été rencontré sur la carte V1.

### Une méthode débouncée ne peut pas être `await`ée

`useDebounce` remplace la méthode par une enveloppe qui **ne retourne rien**.
`await this.refresh()` résout immédiatement sur `undefined`, et
`.catch()` lève. C'est pourquoi `refresh()` reste synchrone et délègue à
`#load()`, qui gère ses propres erreurs : un
rejet non capturé deviendrait une _unhandled promise rejection_ silencieuse.

### MapLibre est chargé dynamiquement

```typescript
const { Map, Marker, NavigationControl } = await import("maplibre-gl")
```

MapLibre pèse 21 Mo sur disque. L'import statique le placerait dans le bundle
de toutes les pages, y compris l'accueil et la fiche objet qui n'affichent
aucune carte.

### La couleur suit le geste, pas le lieu

Un même acteur s'affiche en bleu si l'usager a choisi « donner » et en brun
s'il a choisi « revendre ». La couleur vient donc du template
(`--qfa-geste-color`, alimenté par `GroupeAction.couleur` en base), jamais
d'une propriété du lieu. Seul le Bonus Réparation prend le pas.

## Accessibilité

Une carte MapLibre n'est ni navigable au clavier ni lisible par un lecteur
d'écran. Le composant rend donc **toujours** une liste des lieux côté serveur,
qui reste le chemin accessible tant que la bascule liste/carte n'existe pas.

Les messages d'état (« aucun lieu », « zoomez sur la carte ») sont annoncés via
un conteneur `role="status" aria-live="polite"` présent dès le chargement :
injecté après coup, il ne serait pas annoncé par certains lecteurs d'écran.

`role="status"` plutôt que `role="alert"` : l'information est utile, pas
urgente, et `alert` interromprait la lecture en cours.

### Le worker MapLibre est un bundle à part

Depuis MapLibre 6, l'URL du worker se résout via `import.meta.url`, que Parcel
ne conserve pas : le gabarit la fournit
(`data-assistant-carte-worker-url-value="{% static 'maplibre-worker.js' %}"`)
et le contrôleur la passe à `setWorkerUrl`. Le fichier vient d'une cible Parcel
dédiée (`worker`, contexte `web-worker`, voir `package.json`). Symptôme quand
ça manque : style chargé, punaises visibles, aucune tuile, et
`Cannot find module` dans la console du worker.

## Les punaises sont des liens

Chaque punaise est un `<a>` vers `assistant:lieu`, la fiche du lieu
(maquette 30141:9303) : ouvrable dans un nouvel onglet, utilisable sans
JavaScript. `parametres_lieu` y ajoute le parcours pour que « revenir aux
solutions » retrouve le geste et l'adresse. `pinpoint.ts` sait aussi rendre un
`<button>` quand aucune URL n'est fournie, ce qui n'arrive plus depuis que la
page existe.
